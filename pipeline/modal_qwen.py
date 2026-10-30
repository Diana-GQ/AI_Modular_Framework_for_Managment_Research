"""The open-weight judge's dedicated deployment on Modal (design, Section 2.2).

Qwen3-8B at a pinned commit, served by vLLM from its official image pinned by
digest, on one H100 GPU (the "!" stops Modal from substituting another GPU),
in batch-invariant mode (VLLM_BATCH_INVARIANT=1) with prefix caching off. The
project calls the class directly through Modal, so there is no public endpoint,
and the caller decides how requests are batched. Weights and vLLM's compiled
kernels are kept in Modal volumes. Document text is never written to logs.

    uv run modal run pipeline/modal_qwen.py::main      # the engine's Python interface (no GPU)
    uv run modal run pipeline/modal_qwen.py::fetch     # the pinned weights, into the volume (no GPU)
    uv run modal run pipeline/modal_qwen.py::smoke     # one synthetic request on the GPU
"""

import modal

APP_NAME = "compai-qwen3-8b"
IMAGE = "vllm/vllm-openai:v0.30.0@sha256:8a69ffad015f138d7170c4ddc429e230a3bc1c1719f67e14324749df200a4b90"
MODEL = "Qwen/Qwen3-8B"
REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
GPU = "H100!"

# The official image has python3 but no "python" command, which Modal needs to
# detect the Python version; the link points it at the image's own Python.
image = modal.Image.from_registry(
    IMAGE, setup_dockerfile_commands=['RUN ln -sf "$(command -v python3)" /usr/local/bin/python'],
# Compiled kernels go to the vLLM cache volume, so that later containers reuse them.
).entrypoint([]).env({
    "VLLM_BATCH_INVARIANT": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "VLLM_NO_USAGE_STATS": "1",
    "TORCHINDUCTOR_CACHE_DIR": "/root/.cache/vllm/inductor",
    "TRITON_CACHE_DIR": "/root/.cache/vllm/triton",
})
hf_cache = modal.Volume.from_name("compai-hf-cache", create_if_missing=True)
# vLLM's compiled kernels, kept between containers so that each start does not recompile.
vllm_cache = modal.Volume.from_name("compai-vllm-cache", create_if_missing=True)
app = modal.App(APP_NAME)


@app.function(image=image, timeout=600)
def introspect() -> dict:
    import inspect
    import sys

    import vllm
    from vllm import LLM, SamplingParams

    out = {"vllm": vllm.__version__, "python": sys.version.split()[0],
           "SamplingParams": str(inspect.signature(SamplingParams)),
           "LLM.__init__": str(inspect.signature(LLM.__init__)),
           "LLM.chat": str(inspect.signature(LLM.chat))}
    import vllm.sampling_params as sp
    out["sampling_params names"] = [n for n in dir(sp) if "Param" in n or "Structured" in n or "Guided" in n]
    for name in ("StructuredOutputsParams", "GuidedDecodingParams"):
        cls = getattr(sp, name, None)
        out[name] = str(inspect.signature(cls)) if cls else None
    return out


@app.function(image=image, volumes={"/root/.cache/huggingface": hf_cache}, timeout=60 * 60, cpu=2)
def download() -> dict:
    """Fetch the pinned weights into the volume on a CPU, so the GPU is not billed while they download."""
    import os

    from huggingface_hub import snapshot_download

    path = snapshot_download(MODEL, revision=REVISION)
    hf_cache.commit()
    files = sorted(os.listdir(path))
    return {"model": MODEL, "revision": REVISION, "files": len(files),
            "gigabytes": round(sum(os.path.getsize(os.path.join(path, f)) for f in files) / 1e9, 2)}


@app.cls(image=image, gpu=GPU, volumes={"/root/.cache/huggingface": hf_cache, "/root/.cache/vllm": vllm_cache},
         timeout=60 * 60, scaledown_window=120)
class QwenJudge:
    """Loads the pinned model once per container; generate() runs one batch."""

    @modal.enter()
    def load(self):
        import os

        os.environ["HF_HUB_OFFLINE"] = "1"  # the weights are in the volume; no call to Hugging Face during a run
        from vllm import LLM

        self.llm = LLM(model=MODEL, revision=REVISION, tokenizer_revision=REVISION, seed=0, dtype="bfloat16",
                       max_model_len=16384, enable_prefix_caching=False, gpu_memory_utilization=0.90,
                       structured_outputs_config={"backend": "xgrammar"})
        hf_cache.commit()
        vllm_cache.commit()

    @modal.method()
    def generate(self, requests: list[dict]) -> list[dict]:
        """Each request: chat messages, sampling settings (with its own seed) and
        the structured-output options that constrain the answer, or None for
        plain text. Thinking is switched off. The requests run as one batch."""
        from vllm import SamplingParams
        from vllm.sampling_params import StructuredOutputsParams

        params = [SamplingParams(**r["sampling"], structured_outputs=(
                      StructuredOutputsParams(**r["structured_outputs"]) if r["structured_outputs"] else None))
                  for r in requests]
        outputs = self.llm.chat([r["messages"] for r in requests], sampling_params=params, use_tqdm=False,
                                chat_template_kwargs={"enable_thinking": False})
        results = []
        for out in outputs:
            o = out.outputs[0]
            results.append({"text": o.text, "token_ids": list(o.token_ids), "finish_reason": o.finish_reason,
                            "prompt_tokens": len(out.prompt_token_ids), "output_tokens": len(o.token_ids),
                            "model": MODEL, "revision": REVISION})
        return results

    @modal.method()
    def environment(self) -> dict:
        import os
        import subprocess

        import torch
        import vllm

        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True).stdout.strip()
        config = getattr(self.llm.llm_engine, "vllm_config", None)
        return {"image": IMAGE, "model": MODEL, "revision": REVISION, "vllm": str(vllm.__version__),
                "torch": str(torch.__version__), "cuda": str(torch.version.cuda), "gpu": gpu,
                "batch_invariant": os.environ.get("VLLM_BATCH_INVARIANT"),
                "engine_watermarking": str(getattr(config, "watermarking_config", None)),
                "prefix_caching": str(getattr(getattr(config, "cache_config", None), "enable_prefix_caching", None)),
                "modal_cloud": os.environ.get("MODAL_CLOUD_PROVIDER"), "modal_region": os.environ.get("MODAL_REGION"),
                "container_id": os.environ.get("MODAL_TASK_ID")}


@app.local_entrypoint()
def main():
    import json
    print(json.dumps(introspect.remote(), indent=1))


@app.local_entrypoint()
def fetch():
    import json
    print(json.dumps(download.remote(), indent=1))


@app.local_entrypoint()
def smoke():
    """A synthetic request, with no project data, to check loading and structured output."""
    import json
    judge = QwenJudge()
    print(json.dumps(judge.environment.remote(), indent=1))
    sampling = {"temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0, "watermarking": False, "seed": 1}
    score = {"messages": [{"role": "user", "content": "Rate the idea of selling umbrellas in a rainy city from 1 to 10."}],
             "sampling": dict(sampling, max_tokens=32), "structured_outputs": {"regex": '\\{"score": (10|[1-9])\\}'}}
    written = {"messages": [{"role": "user", "content": "In three short lines, list risks of selling umbrellas."}],
               "sampling": dict(sampling, max_tokens=200), "structured_outputs": None}
    for out in judge.generate.remote([score, score, written]):
        print(json.dumps({k: out[k] for k in ("text", "finish_reason", "output_tokens")}))
