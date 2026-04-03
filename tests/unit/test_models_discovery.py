# tests/unit/test_models_discovery.py
from datetime import datetime, timezone

from netbox_skill.models.common import DeviceTarget
from netbox_skill.models.discovery import (
    MACEntry,
    ARPEntry,
    LLDPNeighbor,
    InterfaceDetail,
    VLANInfo,
    DeviceInfo,
    DiscoveryResult,
)


def test_mac_entry():
    entry = MACEntry(mac="AA:BB:CC:DD:EE:FF", port="Gi0/1", vlan=100)
    assert entry.mac == "AA:BB:CC:DD:EE:FF"
    assert entry.vlan == 100


def test_mac_entry_no_vlan():
    entry = MACEntry(mac="AA:BB:CC:DD:EE:FF", port="Gi0/1")
    assert entry.vlan is None


def test_arp_entry():
    entry = ARPEntry(ip="10.0.0.1", mac="AA:BB:CC:DD:EE:FF", interface="vlan100")
    assert entry.ip == "10.0.0.1"


def test_lldp_neighbor():
    n = LLDPNeighbor(
        local_port="Ethernet1",
        remote_device="sw-core-01",
        remote_port="Ethernet48",
        remote_chassis_id="AA:BB:CC:DD:EE:FF",
    )
    assert n.remote_device == "sw-core-01"


def test_lldp_neighbor_no_chassis():
    n = LLDPNeighbor(
        local_port="Ethernet1", remote_device="sw2", remote_port="Ethernet1"
    )
    assert n.remote_chassis_id is None


def test_interface_detail():
    iface = InterfaceDetail(
        name="Ethernet1",
        status="up",
        speed="10G",
        mtu=9000,
        description="uplink",
        vlans=[100, 200],
    )
    assert iface.name == "Ethernet1"
    assert iface.vlans == [100, 200]


def test_interface_detail_minimal():
    iface = InterfaceDetail(name="Ethernet1", status="down")
    assert iface.speed is None
    assert iface.vlans == []


def test_vlan_info():
    vlan = VLANInfo(id=100, name="mgmt", ports=["Gi0/1", "Gi0/2"])
    assert vlan.id == 100
    assert len(vlan.ports) == 2


def test_device_info():
    info = DeviceInfo(
        hostname="sw-core-01",
        model="SN2700",
        serial="ABC123",
        firmware="SONiC.4.0.0",
    )
    assert info.hostname == "sw-core-01"


def test_device_info_minimal():
    info = DeviceInfo(hostname="unknown")
    assert info.model is None
    assert info.serial is None
    assert info.firmware is None


def test_discovery_result():
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = DiscoveryResult(
        target=target,
        device_info=DeviceInfo(hostname="sw1"),
        mac_table=[MACEntry(mac="AA:BB:CC:DD:EE:FF", port="Ethernet1", vlan=100)],
        arp_table=[],
        lldp_neighbors=[],
        interfaces=[],
        vlans=[],
        errors=[],
        timestamp=datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert result.target.host == "10.0.0.1"
    assert len(result.mac_table) == 1
    assert result.device_info.hostname == "sw1"


def test_discovery_result_with_errors():
    target = DeviceTarget(host="10.0.0.2", platform="netgear")
    result = DiscoveryResult(
        target=target,
        timestamp=datetime.now(timezone.utc),
        errors=["Failed to get ARP table: timeout"],
    )
    assert len(result.errors) == 1
    assert result.device_info is None
    assert result.mac_table == []
