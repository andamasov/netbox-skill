"""FS.com switch CLI output parser (Broadcom-based)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)
from netbox_skill.parsers.registry import DeviceParser, register_parser

if TYPE_CHECKING:
    from netbox_skill.clients.ssh import SSHClient


@register_parser("fs_com")
class FSComParser(DeviceParser):

    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]:
        output = await client.execute("show mac address-table")
        entries = []
        for line in output.splitlines():
            m = re.match(r"(\d+)\s+([\w:]+)\s+\w+\s+(\S+)", line.strip())
            if m:
                entries.append(
                    MACEntry(vlan=int(m.group(1)), mac=m.group(2), port=m.group(3))
                )
        return entries

    async def get_arp_table(self, client: SSHClient) -> list[ARPEntry]:
        output = await client.execute("show arp")
        entries = []
        for line in output.splitlines():
            m = re.match(
                r"Internet\s+(\d+\.\d+\.\d+\.\d+)\s+\S+\s+([\w:]+)\s+\w+\s+(\S+)",
                line.strip(),
            )
            if m:
                entries.append(
                    ARPEntry(ip=m.group(1), mac=m.group(2), interface=m.group(3))
                )
        return entries

    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]:
        output = await client.execute("show lldp neighbors")
        neighbors = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+(\S+)\s+\d+\s+\S+\s+(\S+)",
                line.strip(),
            )
            if m and not line.strip().startswith(("Device", "Capability", "(", "Total", "-")):
                neighbors.append(
                    LLDPNeighbor(
                        local_port=m.group(2),
                        remote_device=m.group(1),
                        remote_port=m.group(3),
                    )
                )
        return neighbors

    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]:
        output = await client.execute("show interface status")
        interfaces = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+\S*\s+(connected|notconnect|disabled|err-disabled)\s+(\S+)\s+(\S+)\s+(\S+)",
                line.strip(),
            )
            if m and not line.strip().startswith(("Port", "-")):
                status_raw = m.group(2)
                status = "up" if status_raw == "connected" else "down"
                speed_raw = m.group(5)
                speed_match = re.search(r"(\d+)", speed_raw)
                speed = f"{speed_match.group(1)}M" if speed_match else None
                interfaces.append(
                    InterfaceDetail(
                        name=m.group(1),
                        status=status,
                        speed=speed,
                    )
                )
        return interfaces

    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]:
        output = await client.execute("show vlan")
        vlans = []
        for line in output.splitlines():
            m = re.match(r"(\d+)\s+(\S+(?:\s+\S+)*?)\s{2,}(active|act/unsup)", line.strip())
            if m and not line.strip().startswith(("VLAN", "----")):
                vlans.append(
                    VLANInfo(id=int(m.group(1)), name=m.group(2).strip(), ports=[])
                )
        return vlans

    async def get_device_info(self, client: SSHClient) -> DeviceInfo:
        output = await client.execute("show version")
        hostname = "unknown"
        model = None
        serial = None
        firmware = None
        for line in output.splitlines():
            m = re.match(r"System Name:\s*(.+)", line)
            if m:
                hostname = m.group(1).strip()
            m = re.match(r"Serial Number:\s*(.+)", line)
            if m:
                serial = m.group(1).strip()
            m = re.match(r".+Software,\s*Version\s*(.+)", line)
            if m:
                firmware = m.group(1).strip()
        return DeviceInfo(
            hostname=hostname, model=model, serial=serial, firmware=firmware
        )
