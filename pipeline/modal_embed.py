"""The embedders' deployment on Modal (design, Section 3).

Each embedding model runs at a pinned commit through sentence-transformers, in
a container image with pinned packages, on one L40S GPU. Texts are encoded one
at a time with deterministic settings, so a text's vector never depends on what
else is encoded with it. Weights are cached in a Modal volume; the container makes no
call to Hugging Face during a run. Document text is never written to logs.

    uv run modal run pipeline/modal_embed.py::main      # the packages' interfaces (no GPU)
    uv run modal run pipeline/modal_embed.py::fetch     # the pinned weights, into the volume (no GPU)
"""

import modal

APP_NAME = "compai-embedders"
GPU = "L40S"
PACKAGES = ["torch==2.14.1", "transformers==5.19.0", "sentence-transformers==6.1.0", "numpy==2.5.4"]
MODELS = {
    "Qwen/Qwen3-Embedding-8B": "1d8ad4ca9b3dd8059ad90a75d4983776a23d44af",
    "BAAI/bge-m3": "5617a9f61b028005a4858fdac845db406aefb181",
    "Alibaba-NLP/gte-modernbert-base": "e7f32e3c00f91d699e8c43b53106206bcc72bb22",
}

image = (modal.Image.debian_slim(python_version="3.12")
         .uv_pip_install(*PACKAGES)
         .env({"HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false",
               "CUBLAS_WORKSPACE_CONFIG": ":4096:8"}))
hf_cache = modal.Volume.from_name("compai-hf-cache", create_if_missing=True)
app = modal.App(APP_NAME)


@app.function(image=image, timeout=600)
def introspect() -> dict:
    import inspect

    import sentence_transformers
    import torch
    import transformers
    from sentence_transformers import SentenceTransformer

    return {"torch": str(torch.__version__), "transformers": str(transformers.__version__),
            "sentence_transformers": str(sentence_transformers.__version__),
            "init": str(inspect.signature(SentenceTransformer.__init__)),
            "encode": str(inspect.signature(SentenceTransformer.encode))}


@app.function(image=image, volumes={"/root/.cache/huggingface": hf_cache}, timeout=60 * 60, cpu=2)
def download() -> dict:
    """Fetch the pinned weights into the volume on a CPU, so the GPU is not billed while they download."""
    from huggingface_hub import snapshot_download

    out = {}
    for model, revision in MODELS.items():
        out[model] = snapshot_download(model, revision=revision)
    hf_cache.commit()
    return out


@app.cls(image=image, gpu=GPU, volumes={"/root/.cache/huggingface": hf_cache}, timeout=60 * 60, scaledown_window=60)
class Embedder:
    model_id: str = modal.parameter()
    revision: str = modal.parameter()
    dtype: str = modal.parameter(default="float32")
    max_seq_length: int = modal.parameter(default=8192)

    @modal.enter()
    def load(self):
        import os

        os.environ["HF_HUB_OFFLINE"] = "1"
        import torch
        from sentence_transformers import SentenceTransformer

        torch.use_deterministic_algorithms(True, warn_only=True)
        torch.backends.cudnn.benchmark = False
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        if MODELS.get(self.model_id) != self.revision:
            raise ValueError("model or revision not pinned in this deployment")
        self.model = SentenceTransformer(self.model_id, revision=self.revision, device="cuda",
                                         model_kwargs={"dtype": getattr(torch, self.dtype)})
        self.model.max_seq_length = self.max_seq_length

    @modal.method()
    def embed(self, texts: list[str], prompt: str | None) -> dict:
        """One text at a time; L2-normalized float32 vectors, as a NumPy file's bytes."""
        import io

        import numpy as np

        tokens, vectors = [], []
        for text in texts:
            tokens.append(int(self.model.tokenize([text])["input_ids"].shape[-1]))
            vectors.append(self.model.encode([text], prompt=prompt, normalize_embeddings=True, batch_size=1,
                                             convert_to_numpy=True)[0])
        buffer = io.BytesIO()
        np.save(buffer, np.vstack(vectors).astype(np.float32), allow_pickle=False)
        return {"npy": buffer.getvalue(), "tokens": tokens}

    @modal.method()
    def environment(self) -> dict:
        import os
        import subprocess

        import sentence_transformers
        import torch
        import transformers

        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True).stdout.strip()
        return {"model": self.model_id, "revision": self.revision, "dtype": self.dtype,
                "max_seq_length": self.max_seq_length, "packages": PACKAGES,
                "torch": str(torch.__version__), "cuda": str(torch.version.cuda),
                "transformers": str(transformers.__version__),
                "sentence_transformers": str(sentence_transformers.__version__), "gpu": gpu,
                "modal_cloud": os.environ.get("MODAL_CLOUD_PROVIDER"), "modal_region": os.environ.get("MODAL_REGION"),
                "container_id": os.environ.get("MODAL_TASK_ID"), "image_id": os.environ.get("MODAL_IMAGE_ID")}


@app.local_entrypoint()
def main():
    import json
    print(json.dumps(introspect.remote(), indent=1))


@app.local_entrypoint()
def fetch():
    import json
    print(json.dumps(download.remote(), indent=1))
