"""Exception hierarchy for netbox-skill."""

from __future__ import annotations

from typing import Any


class NetBoxSkillError(Exception):
    """Base exception for all netbox-skill errors."""


class NetBoxClientError(NetBoxSkillError):
    """Error communicating with the NetBox API."""

    def __init__(
        self,
        status_code: int,
        body: Any = None,
        message: str = "NetBox API error",
    ):
        self.status_code = status_code
        self.body = body
        super().__init__(f"{message} (HTTP {status_code}): {body}")


class NetBoxAuthError(NetBoxClientError):
    """Authentication or authorization failure (401/403)."""


class NetBoxNotFoundError(NetBoxClientError):
    """Resource not found (404)."""


class NetBoxValidationError(NetBoxClientError):
    """Validation error (400) with field-level details."""

    def __init__(
        self,
        status_code: int = 400,
        body: Any = None,
        message: str = "Validation failed",
    ):
        super().__init__(status_code=status_code, body=body, message=message)
        self.field_errors: dict[str, list[str]] = body if isinstance(body, dict) else {}


class NetBoxServerError(NetBoxClientError):
    """Server-side error (5xx)."""


class DeviceError(NetBoxSkillError):
    """Error interacting with a network device."""


class DeviceConnectionError(DeviceError):
    """SSH connection failure (timeout, refused, auth)."""


class CommandError(DeviceError):
    """Command execution failed or returned unexpected output."""


class UnknownPlatformError(DeviceError):
    """No parser registered for the given platform string."""

    def __init__(self, platform: str):
        self.platform = platform
        super().__init__(f"No parser registered for platform: {platform}")


class VisionError(NetBoxSkillError):
    """Error in vision processing."""


class VisionProviderError(VisionError):
    """API call to vision provider failed."""


class ImageProcessingError(VisionError):
    """Image decode, crop, or annotation failure."""


class ConfigError(NetBoxSkillError):
    """Missing or invalid configuration."""
