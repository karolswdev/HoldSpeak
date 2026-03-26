"""TUI utility functions."""


def clamp01(value: float) -> float:
    """Clamp a value between 0.0 and 1.0."""
    return 0.0 if value < 0.0 else 1.0 if value > 1.0 else value
