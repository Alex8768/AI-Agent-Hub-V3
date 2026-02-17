"""
Hardware accelerator detection & memory utilities.
Single source of truth for device selection and cache cleanup.

Design goals:
- Works on macOS / Windows / Linux
- Torch is optional (graceful degradation)
- Centralizes device selection: cuda / mps / cpu
- Centralizes cache cleanup (no direct torch.mps/cuda calls elsewhere)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

DeviceType = Literal["cpu", "cuda", "mps"]


@dataclass(frozen=True)
class AcceleratorState:
    device: DeviceType
    device_name: str
    torch_available: bool


class Accelerator:
    """
    Runtime hardware detector with graceful degradation.
    """

    def __init__(self) -> None:
        self._state: Optional[AcceleratorState] = None

    def _detect(self) -> AcceleratorState:
        try:
            import torch  # type: ignore
        except Exception:
            return AcceleratorState(device="cpu", device_name="CPU", torch_available=False)

        # Prefer CUDA first for most server deployments
        if getattr(torch, "cuda", None) is not None and torch.cuda.is_available():
            name = "NVIDIA CUDA"
            try:
                name = torch.cuda.get_device_name(0)
            except Exception:
                pass
            return AcceleratorState(device="cuda", device_name=name, torch_available=True)

        # Apple Silicon MPS
        if getattr(torch, "backends", None) is not None and getattr(torch.backends, "mps", None) is not None:
            try:
                if torch.backends.mps.is_available():
                    return AcceleratorState(device="mps", device_name="Apple Silicon (MPS)", torch_available=True)
            except Exception:
                pass

        return AcceleratorState(device="cpu", device_name="CPU", torch_available=True)

    @property
    def state(self) -> AcceleratorState:
        if self._state is None:
            self._state = self._detect()
        return self._state

    @property
    def device(self) -> DeviceType:
        return self.state.device

    @property
    def device_name(self) -> str:
        return self.state.device_name

    @property
    def torch_available(self) -> bool:
        return self.state.torch_available

    def empty_cache(self) -> None:
        """
        Best-effort cache cleanup for GPU backends.
        No-op on CPU. Safe if torch is missing.
        """
        if not self.torch_available:
            return
        try:
            import torch  # type: ignore
        except Exception:
            return

        try:
            if self.device == "cuda" and getattr(torch, "cuda", None) is not None:
                torch.cuda.empty_cache()
            elif self.device == "mps":
                # MPS exists only on macOS builds; still guard
                if getattr(torch, "mps", None) is not None:
                    torch.mps.empty_cache()
        except Exception:
            # Non-fatal
            return

    def recommended_batch_size(self, base: int = 32) -> int:
        """
        Small heuristic for safe defaults.
        - CPU: smaller batches
        - MPS/CUDA: base
        """
        if self.device == "cpu":
            return max(1, base // 2)
        return base


# Global singleton
accelerator = Accelerator()
