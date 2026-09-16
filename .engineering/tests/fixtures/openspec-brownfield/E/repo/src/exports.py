"""Export behavior."""


def export_rows(rows: list[str]) -> str:
    """Serialize the current synchronous export."""
    return "\n".join(rows)
