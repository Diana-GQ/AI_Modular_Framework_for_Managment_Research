"""What the AI judges' clients share: prompt files, the two parts of the user
message, and the error raised when a response comes from another model. Each
provider has its own client (pipeline/claude_client.py, pipeline/qwen_client.py),
so that a change to one judge's client never changes the other judge's
configuration hash."""

from pathlib import Path


class ModelMismatch(Exception):
    """A response came from a model other than the one requested."""


def load_prompts(path: Path) -> dict:
    import yaml
    return yaml.safe_load(Path(path).read_text())


def user_blocks(template_prefix: str, document: str, question_template: str, question: str) -> tuple[str, str]:
    """The user message in two parts: the document part, which is the same for
    every question asked about a summary (and so can be cached), and the
    question part. Together they are exactly the specified prompt."""
    return template_prefix.format(document=document), question_template.format(question=question)
