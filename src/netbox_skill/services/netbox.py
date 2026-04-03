"""NetBox service — business logic over the NetBox API client."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from netbox_skill.models.common import BulkResult
from netbox_skill.models.netbox import (
    Cable,
    CableCreate,
    Device,
    DeviceCreate,
    DeviceType,
    DeviceUpdate,
    Interface,
    InterfaceCreate,
    IPAddress,
    IPAddressCreate,
    Prefix,
    Rack,
    Site,
    VLAN,
)

if TYPE_CHECKING:
    from netbox_skill.clients.netbox import NetBoxClient


class NetBoxService:
    def __init__(self, client: NetBoxClient):
        self._client = client

    # --- Device CRUD ---

    async def get_devices(self, **filters: Any) -> list[Device]:
        data = await self._client.get_all("dcim/devices/", params=filters or None)
        return [Device.model_validate(d) for d in data]

    async def create_device(self, data: DeviceCreate) -> Device:
        result = await self._client.create(
            "dcim/devices/", data=data.model_dump(exclude_none=True)
        )
        return Device.model_validate(result)

    async def update_device(self, id: int, data: DeviceUpdate) -> Device:
        result = await self._client.update(
            "dcim/devices/", id=id, data=data.model_dump(exclude_none=True)
        )
        return Device.model_validate(result)

    async def delete_device(self, id: int) -> None:
        await self._client.delete("dcim/devices/", id=id)

    # --- Interface CRUD ---

    async def get_interfaces(self, **filters: Any) -> list[Interface]:
        data = await self._client.get_all("dcim/interfaces/", params=filters or None)
        return [Interface.model_validate(d) for d in data]

    async def create_interface(self, data: InterfaceCreate) -> Interface:
        result = await self._client.create(
            "dcim/interfaces/", data=data.model_dump(exclude_none=True)
        )
        return Interface.model_validate(result)

    # --- IP Address CRUD ---

    async def get_ip_addresses(self, **filters: Any) -> list[IPAddress]:
        data = await self._client.get_all("ipam/ip-addresses/", params=filters or None)
        return [IPAddress.model_validate(d) for d in data]

    async def create_ip_address(self, data: IPAddressCreate) -> IPAddress:
        result = await self._client.create(
            "ipam/ip-addresses/", data=data.model_dump(exclude_none=True)
        )
        return IPAddress.model_validate(result)

    # --- VLAN CRUD ---

    async def get_vlans(self, **filters: Any) -> list[VLAN]:
        data = await self._client.get_all("ipam/vlans/", params=filters or None)
        return [VLAN.model_validate(d) for d in data]

    # --- Cable CRUD ---

    async def get_cables(self, **filters: Any) -> list[Cable]:
        data = await self._client.get_all("dcim/cables/", params=filters or None)
        return [Cable.model_validate(d) for d in data]

    async def create_cable(self, data: CableCreate) -> Cable:
        result = await self._client.create(
            "dcim/cables/", data=data.model_dump(exclude_none=True)
        )
        return Cable.model_validate(result)

    # --- Site, Rack, DeviceType ---

    async def get_sites(self, **filters: Any) -> list[Site]:
        data = await self._client.get_all("dcim/sites/", params=filters or None)
        return [Site.model_validate(d) for d in data]

    async def get_racks(self, **filters: Any) -> list[Rack]:
        data = await self._client.get_all("dcim/racks/", params=filters or None)
        return [Rack.model_validate(d) for d in data]

    async def get_device_types(self, **filters: Any) -> list[DeviceType]:
        data = await self._client.get_all("dcim/device-types/", params=filters or None)
        return [DeviceType.model_validate(d) for d in data]

    # --- Higher-level operations ---

    async def find_or_create_device(
        self, data: DeviceCreate, match_fields: list[str]
    ) -> tuple[Device, bool]:
        filters = {f: getattr(data, f) for f in match_fields if getattr(data, f, None) is not None}
        existing = await self.get_devices(**filters)
        if existing:
            return existing[0], False
        device = await self.create_device(data)
        return device, True

    async def find_or_create_interface(
        self, device_id: int, name: str
    ) -> tuple[Interface, bool]:
        existing = await self.get_interfaces(device_id=device_id, name=name)
        if existing:
            return existing[0], False
        data = InterfaceCreate(device=device_id, name=name)
        iface = await self.create_interface(data)
        return iface, True

    async def assign_ip_to_interface(
        self, ip: str, interface_id: int
    ) -> IPAddress:
        data = IPAddressCreate(
            address=ip,
            assigned_object_type="dcim.interface",
            assigned_object_id=interface_id,
        )
        return await self.create_ip_address(data)

    async def create_cable_between(
        self,
        a_type: str,
        a_id: int,
        b_type: str,
        b_id: int,
    ) -> Cable:
        data = CableCreate(
            a_terminations=[{"object_type": a_type, "object_id": a_id}],
            b_terminations=[{"object_type": b_type, "object_id": b_id}],
        )
        return await self.create_cable(data)

    async def get_device_with_interfaces(self, device_id: int) -> dict:
        devices = await self.get_devices(id=device_id)
        interfaces = await self.get_interfaces(device_id=device_id)
        return {
            "device": devices[0] if devices else None,
            "interfaces": interfaces,
        }

    async def bulk_create_or_update(
        self,
        endpoint: str,
        items: list[dict[str, Any]],
        match_fields: list[str],
    ) -> BulkResult:
        existing = await self._client.get_all(endpoint)
        existing_index: dict[tuple, dict] = {}
        for obj in existing:
            key = tuple(obj.get(f) for f in match_fields)
            existing_index[key] = obj

        created = 0
        unchanged = 0
        errors: list[str] = []

        for item in items:
            key = tuple(item.get(f) for f in match_fields)
            if key in existing_index:
                unchanged += 1
            else:
                try:
                    await self._client.create(endpoint, data=item)
                    created += 1
                except Exception as e:
                    errors.append(str(e))

        return BulkResult(created=created, updated=0, unchanged=unchanged, errors=errors)
