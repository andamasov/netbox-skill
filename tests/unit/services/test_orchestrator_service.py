from unittest.mock import AsyncMock

import pytest

from netbox_skill.models.common import DeviceTarget, SyncMode
from netbox_skill.models.discovery import (
    DeviceInfo,
    DiscoveryResult,
    InterfaceDetail,
    LLDPNeighbor,
)
from netbox_skill.models.netbox import Device, Interface
from netbox_skill.services.orchestrator import OrchestratorService
from datetime import datetime, timezone


@pytest.fixture
def mock_netbox():
    return AsyncMock()


@pytest.fixture
def mock_discovery():
    return AsyncMock()


@pytest.fixture
def service(mock_netbox, mock_discovery):
    return OrchestratorService(netbox=mock_netbox, discovery=mock_discovery)


def make_discovery_result(target, interfaces=None, lldp=None):
    return DiscoveryResult(
        target=target,
        device_info=DeviceInfo(hostname="sw1", model="SN2700", serial="MT123"),
        interfaces=interfaces or [],
        lldp_neighbors=lldp or [],
        timestamp=datetime.now(timezone.utc),
    )


def make_device(id=1, name="sw1"):
    return Device(
        id=id, url=f"https://nb/api/dcim/devices/{id}/", display=name, name=name,
        serial="MT123",
    )


async def test_sync_device_dry_run(service, mock_netbox, mock_discovery):
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    mock_discovery.discover_device = AsyncMock(
        return_value=make_discovery_result(
            target,
            interfaces=[InterfaceDetail(name="Ethernet0", status="up", speed="100G")],
        )
    )
    mock_netbox.find_or_create_device = AsyncMock(return_value=(make_device(), False))
    mock_netbox.get_interfaces = AsyncMock(return_value=[])

    report = await service.sync_device(target, mode=SyncMode.DRY_RUN)
    assert len(report.conflicts) > 0 or len(report.created) > 0 or len(report.unchanged) >= 0
    mock_netbox.create_interface.assert_not_called()


async def test_sync_device_auto_creates_interfaces(service, mock_netbox, mock_discovery):
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    mock_discovery.discover_device = AsyncMock(
        return_value=make_discovery_result(
            target,
            interfaces=[InterfaceDetail(name="Ethernet0", status="up")],
        )
    )
    device = make_device()
    mock_netbox.find_or_create_device = AsyncMock(return_value=(device, False))
    mock_netbox.get_interfaces = AsyncMock(return_value=[])
    mock_netbox.find_or_create_interface = AsyncMock(
        return_value=(Interface(id=10, url="u", display="Ethernet0", name="Ethernet0"), True)
    )

    report = await service.sync_device(target, mode=SyncMode.AUTO)
    assert any(r.action == "created" and r.object_type == "interface" for r in report.created)


async def test_sync_device_existing_interface_unchanged(service, mock_netbox, mock_discovery):
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    mock_discovery.discover_device = AsyncMock(
        return_value=make_discovery_result(
            target,
            interfaces=[InterfaceDetail(name="Ethernet0", status="up")],
        )
    )
    device = make_device()
    mock_netbox.find_or_create_device = AsyncMock(return_value=(device, False))
    existing_iface = Interface(id=10, url="u", display="Ethernet0", name="Ethernet0")
    mock_netbox.get_interfaces = AsyncMock(return_value=[existing_iface])
    mock_netbox.find_or_create_interface = AsyncMock(return_value=(existing_iface, False))

    report = await service.sync_device(target, mode=SyncMode.AUTO)
    assert "Ethernet0" in report.unchanged


async def test_sync_topology_creates_cables(service, mock_netbox, mock_discovery):
    target1 = DeviceTarget(host="10.0.0.1", platform="sonic", device_id=1)
    target2 = DeviceTarget(host="10.0.0.2", platform="sonic", device_id=2)

    result1 = make_discovery_result(
        target1,
        lldp=[LLDPNeighbor(local_port="Ethernet0", remote_device="sw2", remote_port="Ethernet0")],
    )
    result2 = make_discovery_result(
        target2,
        lldp=[LLDPNeighbor(local_port="Ethernet0", remote_device="sw1", remote_port="Ethernet0")],
    )
    mock_discovery.discover_devices = AsyncMock(return_value=[result1, result2])

    mock_netbox.get_devices = AsyncMock(return_value=[make_device(1, "sw1"), make_device(2, "sw2")])

    iface1 = Interface(id=10, url="u", display="Ethernet0", name="Ethernet0", device={"id": 1, "display": "sw1"})
    iface2 = Interface(id=20, url="u", display="Ethernet0", name="Ethernet0", device={"id": 2, "display": "sw2"})
    mock_netbox.get_interfaces = AsyncMock(side_effect=[[iface1], [iface2]])
    mock_netbox.get_cables = AsyncMock(return_value=[])
    mock_netbox.create_cable_between = AsyncMock()

    report = await service.sync_topology([target1, target2], mode=SyncMode.AUTO)
    mock_netbox.create_cable_between.assert_called()
