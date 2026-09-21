"""Account access rules."""


def locked(failures: int) -> bool:
    """Return whether failed attempts lock access."""
    return failures >= 10
