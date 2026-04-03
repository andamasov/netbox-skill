from unittest.mock import AsyncMock

import pytest

from netbox_skill.models.netbox import Device, DeviceCreate, DeviceUpdate
from netbox_skill.services.netbox import NetBoxService


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def service(mock_client):
    return NetBoxService(client=mock_client)


DEVICE_RESPONSE = {
    "id": 1,
    "url": "https://netbox.test/api/dcim/devices/1/",
    "display": "sw1",
    "name": "sw1",
    "status": {"value": "active", "label": "Active"},
    "serial": "SN123",
}


async def test_get_devices(service, mock_client):
    mock_client.get_all = AsyncMock(return_value=[DEVICE_RESPONSE])
    devices = await service.get_devices(status="active")
    assert len(devices) == 1
    assert isinstance(devices[0], Device)
    assert devices[0].name == "sw1"
    mock_client.get_all.assert_called_once_with("dcim/devices/", params={"status": "active"})


async def test_create_device(service, mock_client):
    mock_client.create = AsyncMock(return_value=DEVICE_RESPONSE)
    data = DeviceCreate(name="sw1", role=1, device_type=1, site=1)
    device = await service.create_device(data)
    assert isinstance(device, Device)
    assert device.id == 1


async def test_update_device(service, mock_client):
    mock_client.update = AsyncMock(return_value={**DEVICE_RESPONSE, "name": "sw1-renamed"})
    data = DeviceUpdate(name="sw1-renamed")
    device = await service.update_device(1, data)
    assert device.name == "sw1-renamed"


async def test_delete_device(service, mock_client):
    mock_client.delete = AsyncMock()
    await service.delete_device(1)
    mock_client.delete.assert_called_once_with("dcim/devices/", id=1)


async def test_find_or_create_device_exists(service, mock_client):
    mock_client.get_all = AsyncMock(return_value=[DEVICE_RESPONSE])
    data = DeviceCreate(name="sw1", role=1, device_type=1, site=1)
    device, created = await service.find_or_create_device(data, match_fields=["name"])
    assert created is False
    assert device.name == "sw1"


async def test_find_or_create_device_creates(service, mock_client):
    mock_client.get_all = AsyncMock(return_value=[])
    mock_client.create = AsyncMock(return_value=DEVICE_RESPONSE)
    data = DeviceCreate(name="sw1", role=1, device_type=1, site=1)
    device, created = await service.find_or_create_device(data, match_fields=["name"])
    assert created is True
    assert device.id == 1


async def test_find_or_create_interface(service, mock_client):
    iface_resp = {
        "id": 10,
        "url": "https://netbox.test/api/dcim/interfaces/10/",
        "display": "Ethernet1",
        "name": "Ethernet1",
        "device": {"id": 1, "display": "sw1"},
    }
    mock_client.get_all = AsyncMock(return_value=[iface_resp])
    iface, created = await service.find_or_create_interface(device_id=1, name="Ethernet1")
    assert created is False
    assert iface.name == "Ethernet1"


async def test_bulk_create_or_update(service, mock_client):
    existing = [DEVICE_RESPONSE]
    mock_client.get_all = AsyncMock(return_value=existing)
    mock_client.create = AsyncMock(return_value={"id": 2, "url": "u", "display": "sw2", "name": "sw2"})

    items = [
        {"name": "sw1", "role": 1, "device_type": 1, "site": 1},  # exists
        {"name": "sw2", "role": 1, "device_type": 1, "site": 1},  # new
    ]
    result = await service.bulk_create_or_update("dcim/devices/", items, match_fields=["name"])
    assert result.unchanged == 1
    assert result.created == 1
