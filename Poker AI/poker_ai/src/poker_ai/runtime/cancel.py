"""Cooperative cancellation for long-running library work."""


class WorkCancelled(Exception):
    """Raised when ``cancel_check()`` returns True during a pipeline step."""
