"""SONiC CLI output parser for Mellanox/Broadcom switches."""

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


@register_parser("sonic")
class SonicParser(DeviceParser):

    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]:
        output = await client.execute("show mac")
        entries = []
        for line in output.splitlines():
            m = re.match(
                r"\s*\d+\s+(\d+)\s+([\w:]+)\s+(\S+)\s+\w+",
                line,
            )
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
                r"(\d+\.\d+\.\d+\.\d+)\s+([\w:]+)\s+(\S+)",
                line.strip(),
            )
            if m:
                entries.append(
                    ARPEntry(ip=m.group(1), mac=m.group(2), interface=m.group(3))
                )
        return entries

    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]:
        output = await client.execute("show lldp table")
        neighbors = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+(\S+)\s+(\S+)\s+\S+\s+(\S+)",
                line.strip(),
            )
            if m and not line.strip().startswith(("Capability", "LocalPort", "-")):
                neighbors.append(
                    LLDPNeighbor(
                        local_port=m.group(1),
                        remote_device=m.group(2),
                        remote_port=m.group(3),
                        remote_chassis_id=None,
                    )
                )
        return neighbors

    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]:
        output = await client.execute("show interfaces status")
        interfaces = []
        for line in output.splitlines():
            m = re.match(
                r"\s*(\S+)\s+\S+\s+(\S+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+(\w+)\s+(\w+)",
                line,
            )
            if m and not line.strip().startswith(("Interface", "-")):
                interfaces.append(
                    InterfaceDetail(
                        name=m.group(1),
                        speed=m.group(2),
                        mtu=int(m.group(3)),
                        status=m.group(4).lower(),
                    )
                )
        return interfaces

    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]:
        output = await client.execute("show vlan brief")
        vlans: dict[int, VLANInfo] = {}
        current_vlan_id: int | None = None
        for line in output.splitlines():
            vlan_match = re.match(r"\|\s+(\d+)\s+\|", line)
            if vlan_match:
                current_vlan_id = int(vlan_match.group(1))
                if current_vlan_id not in vlans:
                    vlans[current_vlan_id] = VLANInfo(
                        id=current_vlan_id, name=f"Vlan{current_vlan_id}", ports=[]
                    )
            if current_vlan_id is not None:
                port_match = re.findall(r"(Ethernet\d+)", line)
                for port in port_match:
                    if port not in vlans[current_vlan_id].ports:
                        vlans[current_vlan_id].ports.append(port)
        return list(vlans.values())

    async def get_device_info(self, client: SSHClient) -> DeviceInfo:
        output = await client.execute("show platform summary")
        model = None
        serial = None
        hostname = "unknown"
        for line in output.splitlines():
            m = re.match(r"HwSKU:\s*(.+)", line)
            if m:
                model = m.group(1).strip()
            m = re.match(r"Serial Number:\s*(.+)", line)
            if m:
                serial = m.group(1).strip()
        # Try to get hostname
        try:
            hostname_output = await client.execute("hostname")
            hostname = hostname_output.strip() or "unknown"
        except Exception:
            pass
        return DeviceInfo(hostname=hostname, model=model, serial=serial)
