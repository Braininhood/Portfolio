"""Optional PyTorch / safetensors imports (``pip install -e '.[ml]'``)."""

from __future__ import annotations

from typing import Any


def require_torch() -> Any:
    """Return the ``torch`` module or raise with an install hint."""
    try:
        import torch
    except ImportError as exc:
        msg = "HHFormer requires PyTorch. Install with: pip install -e '.[ml]'"
        raise ImportError(msg) from exc
    return torch


def cuda_available() -> bool:
    """True when a CUDA PyTorch wheel is installed and a GPU op succeeds."""
    try:
        torch = require_torch()
    except ImportError:
        return False
    if getattr(torch.version, "cuda", None) is None:
        return False
    try:
        if not torch.cuda.is_available():
            return False
        t = torch.tensor([1.0], device="cuda")
        _ = t * t
        return True
    except (AssertionError, RuntimeError, OSError):
        return False


def save_state_dict_safetensors(state_dict: dict[str, Any], path: str) -> None:
    """Write model weights to a ``.safetensors`` file."""
    try:
        from safetensors.torch import save_file
    except ImportError as exc:
        msg = "HHFormer requires safetensors. Install with: pip install -e '.[ml]'"
        raise ImportError(msg) from exc
    save_file(state_dict, path)
