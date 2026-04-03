from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from netbox_skill.parsers.fs_com import FSComParser
from netbox_skill.parsers.registry import get_parser

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fs_com"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture
def parser():
    return FSComParser()


@pytest.fixture
def mock_client():
    return AsyncMock()


async def test_fs_com_registered():
    parser = get_parser("fs_com")
    assert isinstance(parser, FSComParser)


async def test_parse_mac_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_mac_address_table.txt"))
    entries = await parser.get_mac_table(mock_client)
    assert len(entries) == 3
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"
    assert entries[0].port == "Gi0/1"
    assert entries[0].vlan == 100


async def test_parse_arp_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_arp.txt"))
    entries = await parser.get_arp_table(mock_client)
    assert len(entries) == 3
    assert entries[0].ip == "10.0.0.1"
    assert entries[0].interface == "Vlan100"


async def test_parse_lldp_neighbors(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_lldp_neighbors.txt"))
    neighbors = await parser.get_lldp_neighbors(mock_client)
    assert len(neighbors) == 2
    assert neighbors[0].local_port == "Gi0/1"
    assert neighbors[0].remote_device == "sw-core-01"
    assert neighbors[0].remote_port == "Gi0/48"


async def test_parse_interfaces(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_interface_status.txt"))
    ifaces = await parser.get_interfaces(mock_client)
    assert len(ifaces) == 3
    assert ifaces[0].name == "Gi0/1"
    assert ifaces[0].status == "up"
    assert ifaces[2].status == "down"


async def test_parse_vlans(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_vlan.txt"))
    vlans = await parser.get_vlans(mock_client)
    assert len(vlans) == 3
    assert vlans[1].id == 100
    assert vlans[1].name == "Management"


async def test_parse_device_info(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_version.txt"))
    info = await parser.get_device_info(mock_client)
    assert info.hostname == "sw-dist-01"
    assert info.serial == "FSN123456789"
    assert info.firmware == "2.5.0"
