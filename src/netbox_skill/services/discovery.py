"""Discovery service — SSH into devices and collect operational data."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Protocol, TYPE_CHECKING

from netbox_skill.clients.ssh import SSHClient
from netbox_skill.models.common import CredentialSet, DeviceTarget
from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    DiscoveryResult,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)
from netbox_skill.parsers.registry import get_parser

if TYPE_CHECKING:
    from netbox_skill.services.netbox import NetBoxService


class CredentialResolver(Protocol):
    async def resolve(self, target: DeviceTarget) -> CredentialSet: ...


DATA_TYPE_METHODS = {
    "mac_table": "get_mac_table",
    "arp_table": "get_arp_table",
    "lldp": "get_lldp_neighbors",
    "interfaces": "get_interfaces",
    "vlans": "get_vlans",
    "device_info": "get_device_info",
}


class DiscoveryService:
    def __init__(
        self,
        credential_resolver: CredentialResolver,
        max_concurrent: int = 10,
    ):
        self._credential_resolver = credential_resolver
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def discover_device(
        self,
        target: DeviceTarget,
        data_types: list[str] | None = None,
    ) -> DiscoveryResult:
        creds = await self._credential_resolver.resolve(target)
        parser = get_parser(target.platform)
        types_to_collect = data_types or list(DATA_TYPE_METHODS.keys())

        result_data: dict[str, Any] = {
            "target": target,
            "timestamp": datetime.now(timezone.utc),
            "errors": [],
        }

        async with SSHClient(host=target.host, credentials=creds) as client:
            for data_type in types_to_collect:
                method_name = DATA_TYPE_METHODS.get(data_type)
                if not method_name:
                    continue
                try:
                    value = await getattr(parser, method_name)(client)
                    result_data[data_type] = value
                except Exception as e:
                    result_data["errors"].append(f"{data_type}: {e}")

        return DiscoveryResult(
            target=target,
            device_info=result_data.get("device_info"),
            mac_table=result_data.get("mac_table", []),
            arp_table=result_data.get("arp_table", []),
            lldp_neighbors=result_data.get("lldp", []),
            interfaces=result_data.get("interfaces", []),
            vlans=result_data.get("vlans", []),
            errors=result_data.get("errors", []),
            timestamp=result_data["timestamp"],
        )

    async def discover_devices(
        self,
        targets: list[DeviceTarget],
        data_types: list[str] | None = None,
    ) -> list[DiscoveryResult]:
        async def _limited(target: DeviceTarget) -> DiscoveryResult:
            async with self._semaphore:
                try:
                    return await self.discover_device(target, data_types)
                except Exception as e:
                    return DiscoveryResult(
                        target=target,
                        timestamp=datetime.now(timezone.utc),
                        errors=[str(e)],
                    )

        tasks = [_limited(t) for t in targets]
        return list(await asyncio.gather(*tasks))

    async def discover_from_netbox(
        self,
        netbox: NetBoxService,
        filters: dict[str, Any],
        data_types: list[str] | None = None,
    ) -> list[DiscoveryResult]:
        devices = await netbox.get_devices(**filters)
        targets = []
        for device in devices:
            if device.primary_ip4 and isinstance(device.primary_ip4, dict):
                ip = device.primary_ip4.get("address", "").split("/")[0]
            else:
                continue
            platform_name = ""
            if device.platform and hasattr(device.platform, "slug"):
                platform_name = device.platform.slug or ""
            if not platform_name:
                continue
            targets.append(
                DeviceTarget(
                    host=ip,
                    platform=platform_name,
                    device_id=device.id,
                )
            )
        return await self.discover_devices(targets, data_types)
