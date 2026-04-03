import pytest

from netbox_skill.parsers.registry import (
    DeviceParser,
    PARSER_REGISTRY,
    register_parser,
    get_parser,
)
from netbox_skill.exceptions import UnknownPlatformError
from netbox_skill.clients.ssh import SSHClient
from netbox_skill.models.discovery import (
    MACEntry, ARPEntry, LLDPNeighbor, InterfaceDetail, VLANInfo, DeviceInfo,
)


def test_register_parser():
    @register_parser("test_vendor")
    class TestParser(DeviceParser):
        async def get_mac_table(self, client): return []
        async def get_arp_table(self, client): return []
        async def get_lldp_neighbors(self, client): return []
        async def get_interfaces(self, client): return []
        async def get_vlans(self, client): return []
        async def get_device_info(self, client): return DeviceInfo(hostname="test")

    assert "test_vendor" in PARSER_REGISTRY
    parser = get_parser("test_vendor")
    assert isinstance(parser, TestParser)

    # Cleanup
    del PARSER_REGISTRY["test_vendor"]


def test_get_parser_unknown():
    with pytest.raises(UnknownPlatformError) as exc_info:
        get_parser("nonexistent_platform")
    assert exc_info.value.platform == "nonexistent_platform"


def test_device_parser_is_abstract():
    with pytest.raises(TypeError):
        DeviceParser()
