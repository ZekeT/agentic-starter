"""Fingerprint decisions shared by update planning and legacy conversion."""

from typing import Any

from .ownership import digest, hash_history


def classify(
    local: bytes | None, incoming: bytes, baseline: str | None
) -> tuple[str, str]:
    """Implement the complete update truth table, including absence and convergence."""
    current, offered = digest(local), digest(incoming)
    if current == offered:
        return "PRESERVE", "Already converged with incoming owned content"
    if baseline is None:
        if local is None:
            return "ADD", "New owned scope"
        return "CONFLICT", "Unknown customization; resolve ownership explicitly"
    if offered == baseline:
        return "PRESERVE", "Upstream unchanged; retain local content or deletion"
    if current == baseline:
        return "MERGE", "Pristine local scope; apply upstream change"
    return "CONFLICT", "Local and upstream both changed; baseline remains unchanged"


def legacy_baseline(local: bytes | None, entry: dict[str, Any]) -> str | None:
    """Accept only recorded pristine full-file evidence, never guess customized bases."""
    value = digest(local)
    if value in hash_history(entry, "Legacy file"):
        return value
    return None
