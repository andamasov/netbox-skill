from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from netbox_skill.models.common import CredentialSet, DeviceTarget
from netbox_skill.models.discovery import DeviceInfo, MACEntry, DiscoveryResult
from netbox_skill.services.discovery import DiscoveryService, CredentialResolver


class MockCredentialResolver:
    async def resolve(self, target: DeviceTarget) -> CredentialSet:
        return target.credentials or CredentialSet(username="admin", password="pass")


@pytest.fixture
def service():
    return DiscoveryService(credential_resolver=MockCredentialResolver(), max_concurrent=2)


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_device(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_device_info = AsyncMock(return_value=DeviceInfo(hostname="sw1"))
    mock_parser.get_mac_table = AsyncMock(return_value=[MACEntry(mac="AA:BB:CC:DD:EE:01", port="Eth0", vlan=100)])
    mock_parser.get_arp_table = AsyncMock(return_value=[])
    mock_parser.get_lldp_neighbors = AsyncMock(return_value=[])
    mock_parser.get_interfaces = AsyncMock(return_value=[])
    mock_parser.get_vlans = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = await service.discover_device(target)
    assert isinstance(result, DiscoveryResult)
    assert result.device_info.hostname == "sw1"
    assert len(result.mac_table) == 1
    assert result.errors == []


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_device_selective(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_mac_table = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = await service.discover_device(target, data_types=["mac_table"])
    mock_parser.get_mac_table.assert_called_once()
    mock_parser.get_arp_table.assert_not_called()


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_device_partial_failure(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_device_info = AsyncMock(return_value=DeviceInfo(hostname="sw1"))
    mock_parser.get_mac_table = AsyncMock(side_effect=Exception("timeout"))
    mock_parser.get_arp_table = AsyncMock(return_value=[])
    mock_parser.get_lldp_neighbors = AsyncMock(return_value=[])
    mock_parser.get_interfaces = AsyncMock(return_value=[])
    mock_parser.get_vlans = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = await service.discover_device(target)
    assert len(result.errors) == 1
    assert "timeout" in result.errors[0]
    assert result.mac_table == []


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_devices_concurrent(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_device_info = AsyncMock(return_value=DeviceInfo(hostname="sw"))
    mock_parser.get_mac_table = AsyncMock(return_value=[])
    mock_parser.get_arp_table = AsyncMock(return_value=[])
    mock_parser.get_lldp_neighbors = AsyncMock(return_value=[])
    mock_parser.get_interfaces = AsyncMock(return_value=[])
    mock_parser.get_vlans = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    targets = [
        DeviceTarget(host="10.0.0.1", platform="sonic"),
        DeviceTarget(host="10.0.0.2", platform="sonic"),
        DeviceTarget(host="10.0.0.3", platform="sonic"),
    ]
    results = await service.discover_devices(targets)
    assert len(results) == 3
