"""Vision provider base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from netbox_skill.models.rack_vision import RackContext


class VisionProvider(ABC):
    @abstractmethod
    async def analyze_rack(
        self, image: bytes, prompt: str, context: RackContext
    ) -> dict[str, Any]:
        """Send rack image for analysis. Returns structured JSON response."""
        ...

    @abstractmethod
    async def identify_device(
        self, crop: bytes, prompt: str
    ) -> dict[str, Any]:
        """Send cropped device image for closer identification."""
        ...
