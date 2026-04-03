"""Parser base class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from netbox_skill.exceptions import UnknownPlatformError
from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)

if TYPE_CHECKING:
    from netbox_skill.clients.ssh import SSHClient


class DeviceParser(ABC):
    """Base class all vendor parsers must implement."""

    @abstractmethod
    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]: ...

    @abstractmethod
    async def get_arp_table(self, client: SSHClient) -> list[ARPEntry]: ...

    @abstractmethod
    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]: ...

    @abstractmethod
    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]: ...

    @abstractmethod
    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]: ...

    @abstractmethod
    async def get_device_info(self, client: SSHClient) -> DeviceInfo: ...


PARSER_REGISTRY: dict[str, type[DeviceParser]] = {}


def register_parser(platform: str):
    """Decorator to register a parser class for a platform string."""

    def decorator(cls: type[DeviceParser]) -> type[DeviceParser]:
        PARSER_REGISTRY[platform] = cls
        return cls

    return decorator


def get_parser(platform: str) -> DeviceParser:
    """Instantiate and return the parser for the given platform."""
    cls = PARSER_REGISTRY.get(platform)
    if cls is None:
        raise UnknownPlatformError(platform)
    return cls()
