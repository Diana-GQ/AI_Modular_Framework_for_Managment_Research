"""Framework for building research pipelines from components with explicit contracts.

A component is one packaged AI or code operation. Its contract (contract.yaml)
declares what it takes and returns (typed), everything that can change its
output (pinned), where its outputs live (persisted) and the evidence that it
measures what it claims (validated); its card (card.md) documents it for
readers. The runner enforces the contract and writes a provenance record for
every run (framework, Section 3).
"""
