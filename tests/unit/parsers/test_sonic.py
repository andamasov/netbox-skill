from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from netbox_skill.parsers.sonic import SonicParser
from netbox_skill.parsers.registry import get_parser

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "sonic"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture
def parser():
    return SonicParser()


@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client


async def test_sonic_registered():
    parser = get_parser("sonic")
    assert isinstance(parser, SonicParser)


async def test_parse_mac_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_mac.txt"))
    entries = await parser.get_mac_table(mock_client)
    assert len(entries) == 3
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"
    assert entries[0].port == "Ethernet0"
    assert entries[0].vlan == 100
    assert entries[2].vlan == 200


async def test_parse_arp_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_arp.txt"))
    entries = await parser.get_arp_table(mock_client)
    assert len(entries) == 3
    assert entries[0].ip == "10.0.0.1"
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"
    assert entries[0].interface == "Ethernet0"


async def test_parse_lldp_neighbors(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_lldp_table.txt"))
    neighbors = await parser.get_lldp_neighbors(mock_client)
    assert len(neighbors) == 2
    assert neighbors[0].local_port == "Ethernet0"
    assert neighbors[0].remote_device == "sw-core-01"
    assert neighbors[0].remote_port == "Ethernet48"


async def test_parse_interfaces(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_interfaces_status.txt"))
    ifaces = await parser.get_interfaces(mock_client)
    assert len(ifaces) == 3
    assert ifaces[0].name == "Ethernet0"
    assert ifaces[0].status == "up"
    assert ifaces[0].speed == "100G"
    assert ifaces[0].mtu == 9100
    assert ifaces[2].status == "down"


async def test_parse_vlans(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_vlan_brief.txt"))
    vlans = await parser.get_vlans(mock_client)
    assert len(vlans) == 2
    assert vlans[0].id == 100
    assert "Ethernet0" in vlans[0].ports
    assert "Ethernet4" in vlans[0].ports
    assert vlans[1].id == 200


async def test_parse_device_info(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_platform_summary.txt"))
    info = await parser.get_device_info(mock_client)
    assert info.hostname is not None
    assert info.model == "Mellanox-SN2700"
    assert info.serial == "MT1234567890"
