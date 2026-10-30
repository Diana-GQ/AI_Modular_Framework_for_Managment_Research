"""Methodological checks (framework, Section 6): errors of method that the
pipeline refuses to run with, beyond the type checks of the runner."""

from .contracts import Contract, TypeSpec


class MethodError(Exception):
    """An analysis step that the methodological checks refuse."""


VECTOR_IDENTITY = ("model", "instruction", "postprocessing")


def assert_comparable(a: TypeSpec, b: TypeSpec) -> None:
    """Vectors from different models, instructions or post-processing are
    different types, and comparing them is an error."""
    if a.kind not in ("vector", "matrix") or b.kind not in ("vector", "matrix"):
        raise MethodError("only vectors can be compared by distance")
    differences = [f for f in VECTOR_IDENTITY if getattr(a, f) != getattr(b, f)]
    if differences:
        raise MethodError(f"vectors of different types compared (they differ in {', '.join(differences)})")


def assert_ready_for_inference(contract: Contract) -> None:
    """A component's outputs may enter inference (a regression, a test) only
    once it is validated; a stochastic component also needs a reliability
    estimate with a recorded result."""
    if contract.validated.status != "validated":
        raise MethodError(f"{contract.component} is {contract.validated.status}, not validated")
    if not contract.deterministic:
        reliability = [c for c in contract.validated.checks if c.kind == "reliability" and c.result]
        if not reliability:
            raise MethodError(f"{contract.component} is stochastic and has no reliability estimate")
