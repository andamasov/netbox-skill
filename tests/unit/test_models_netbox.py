# tests/unit/test_models_netbox.py
from netbox_skill.models.netbox import (
    Device,
    DeviceCreate,
    DeviceUpdate,
    Interface,
    InterfaceCreate,
    IPAddress,
    IPAddressCreate,
    Prefix,
    VLAN,
    Cable,
    CableCreate,
    Site,
    Location,
    Rack,
    DeviceType,
    Manufacturer,
    Platform,
    DeviceRole,
    NestedObject,
)


def test_device_from_api_response():
    data = {
        "id": 1,
        "url": "https://netbox/api/dcim/devices/1/",
        "display": "sw-core-01",
        "name": "sw-core-01",
        "status": {"value": "active", "label": "Active"},
        "site": {"id": 1, "url": "https://netbox/api/dcim/sites/1/", "display": "DC1", "name": "DC1", "slug": "dc1"},
        "device_type": {"id": 5, "display": "SN2700", "manufacturer": {"id": 2, "display": "Mellanox"}},
        "role": {"id": 3, "display": "Core Switch"},
        "serial": "ABC123",
        "custom_fields": {"deployed": "2024-01-01"},
        "created": "2024-01-01T00:00:00Z",
        "last_updated": "2024-06-01T12:00:00Z",
    }
    device = Device.model_validate(data)
    assert device.id == 1
    assert device.name == "sw-core-01"
    assert device.serial == "ABC123"
    assert device.custom_fields == {"deployed": "2024-01-01"}


def test_device_extra_fields_allowed():
    data = {
        "id": 1,
        "url": "https://netbox/api/dcim/devices/1/",
        "display": "sw1",
        "name": "sw1",
        "status": {"value": "active", "label": "Active"},
        "unknown_future_field": "some_value",
    }
    device = Device.model_validate(data)
    assert device.id == 1


def test_device_create():
    create = DeviceCreate(
        name="sw-new-01",
        role=3,
        device_type=5,
        site=1,
        status="active",
    )
    d = create.model_dump(exclude_none=True)
    assert d["name"] == "sw-new-01"
    assert d["role"] == 3


def test_device_update_partial():
    update = DeviceUpdate(name="sw-renamed")
    d = update.model_dump(exclude_none=True)
    assert d == {"name": "sw-renamed"}


def test_interface_from_api():
    data = {
        "id": 10,
        "url": "https://netbox/api/dcim/interfaces/10/",
        "display": "Ethernet1",
        "name": "Ethernet1",
        "device": {"id": 1, "display": "sw1"},
        "type": {"value": "1000base-t", "label": "1000BASE-T"},
        "enabled": True,
        "mtu": 9000,
        "speed": 1000000,
        "description": "uplink",
    }
    iface = Interface.model_validate(data)
    assert iface.name == "Ethernet1"
    assert iface.mtu == 9000


def test_ip_address_from_api():
    data = {
        "id": 100,
        "url": "https://netbox/api/ipam/ip-addresses/100/",
        "display": "10.0.0.1/24",
        "address": "10.0.0.1/24",
        "status": {"value": "active", "label": "Active"},
        "assigned_object_type": "dcim.interface",
        "assigned_object_id": 10,
    }
    ip = IPAddress.model_validate(data)
    assert ip.address == "10.0.0.1/24"
    assert ip.assigned_object_id == 10


def test_cable_create():
    cable = CableCreate(
        a_terminations=[{"object_type": "dcim.interface", "object_id": 1}],
        b_terminations=[{"object_type": "dcim.interface", "object_id": 2}],
    )
    d = cable.model_dump(exclude_none=True)
    assert len(d["a_terminations"]) == 1


def test_nested_object():
    obj = NestedObject(id=1, display="test", url="https://netbox/api/test/1/")
    assert obj.id == 1
    assert obj.display == "test"
