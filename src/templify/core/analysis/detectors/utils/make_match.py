from typing import Callable

def make_match(detector_fn: Callable, *, threshold: float | None = None):
    """
    Factory for a standardized `match` shim.

    Args:
        detector_fn: the real detector function (e.g. detect_lists).
        threshold: optional default threshold to pass through.

    Returns:
        A `match` function with the standardized signature:
            match(lines, features=None, domain=None, **kwargs)
    """
    def match(lines, features=None, domain=None, **kwargs):
        if threshold is not None:
            return detector_fn(lines, threshold=threshold, **kwargs)
        return detector_fn(lines, **kwargs)

    return match
