"""Orchestrator service — discover, diff, populate NetBox."""

from __future__ import annotations

from typing import TYPE_CHECKING

from netbox_skill.models.common import (
    ChangeRecord,
    ConflictRecord,
    DeviceTarget,
    SyncMode,
    SyncReport,
)
from netbox_skill.models.netbox import DeviceCreate

if TYPE_CHECKING:
    from netbox_skill.services.discovery import DiscoveryService
    from netbox_skill.services.netbox import NetBoxService


class OrchestratorService:
    def __init__(self, netbox: NetBoxService, discovery: DiscoveryService):
        self._netbox = netbox
        self._discovery = discovery

    async def sync_device(
        self, target: DeviceTarget, mode: SyncMode
    ) -> SyncReport:
        result = await self._discovery.discover_device(target)
        report = SyncReport(device=target, errors=list(result.errors))

        # Find or create the device in NetBox
        device_data = DeviceCreate(
            name=result.device_info.hostname if result.device_info else target.host,
            role=1,  # Placeholder — caller should set via target or config
            device_type=1,  # Placeholder
            site=1,  # Placeholder
            serial=result.device_info.serial if result.device_info else None,
        )
        device, device_created = await self._netbox.find_or_create_device(
            device_data, match_fields=["name"]
        )
        if device_created:
            report.created.append(
                ChangeRecord(
                    object_type="device",
                    object_id=device.id,
                    action="created",
                    detail={"name": device.name},
                )
            )

        # Sync interfaces
        existing_interfaces = await self._netbox.get_interfaces(device_id=device.id)
        existing_names = {i.name for i in existing_interfaces}

        for iface in result.interfaces:
            if iface.name in existing_names:
                report.unchanged.append(iface.name)
            else:
                if mode == SyncMode.DRY_RUN:
                    report.created.append(
                        ChangeRecord(
                            object_type="interface",
                            action="would_create",
                            detail={"name": iface.name, "device_id": device.id},
                        )
                    )
                else:
                    nb_iface, created = await self._netbox.find_or_create_interface(
                        device_id=device.id, name=iface.name
                    )
                    if created:
                        report.created.append(
                            ChangeRecord(
                                object_type="interface",
                                object_id=nb_iface.id,
                                action="created",
                                detail={"name": iface.name},
                            )
                        )
                    else:
                        report.unchanged.append(iface.name)

        return report

    async def sync_devices(
        self, targets: list[DeviceTarget], mode: SyncMode
    ) -> list[SyncReport]:
        reports = []
        for target in targets:
            try:
                report = await self.sync_device(target, mode)
                reports.append(report)
            except Exception as e:
                reports.append(SyncReport(device=target, errors=[str(e)]))
        return reports

    async def sync_topology(
        self, targets: list[DeviceTarget], mode: SyncMode
    ) -> SyncReport:
        report = SyncReport(device=targets[0] if targets else DeviceTarget(host="", platform=""))

        results = await self._discovery.discover_devices(targets)

        # Build hostname → device_id mapping
        all_devices = await self._netbox.get_devices()
        name_to_device = {d.name: d for d in all_devices}

        # Cache interfaces per device_id to avoid redundant fetches
        iface_cache: dict[int, dict[str, object]] = {}

        async def get_iface_map(device_id: int) -> dict[str, object]:
            if device_id not in iface_cache:
                ifaces = await self._netbox.get_interfaces(device_id=device_id)
                iface_cache[device_id] = {i.name: i for i in ifaces}
            return iface_cache[device_id]

        for result in results:
            if not result.device_info:
                continue
            local_device = name_to_device.get(result.device_info.hostname)
            if not local_device:
                continue

            local_iface_map = await get_iface_map(local_device.id)

            for neighbor in result.lldp_neighbors:
                local_iface = local_iface_map.get(neighbor.local_port)
                remote_device = name_to_device.get(neighbor.remote_device)
                if not local_iface or not remote_device:
                    continue

                remote_iface_map = await get_iface_map(remote_device.id)
                remote_iface = remote_iface_map.get(neighbor.remote_port)
                if not remote_iface:
                    continue

                if mode != SyncMode.DRY_RUN:
                    await self._netbox.create_cable_between(
                        "dcim.interface", local_iface.id,
                        "dcim.interface", remote_iface.id,
                    )
                    report.created.append(
                        ChangeRecord(
                            object_type="cable",
                            action="created",
                            detail={
                                "a": f"{local_device.name}:{neighbor.local_port}",
                                "b": f"{remote_device.name}:{neighbor.remote_port}",
                            },
                        )
                    )

        return report
