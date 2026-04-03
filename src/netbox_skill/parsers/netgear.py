"""Netgear managed switch CLI output parser."""

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


@register_parser("netgear")
class NetgearParser(DeviceParser):

    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]:
        output = await client.execute("show mac-address-table")
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
                r"(\d+\.\d+\.\d+\.\d+)\s+([\w:]+)\s+(\S.*\S)",
                line.strip(),
            )
            if m:
                entries.append(
                    ARPEntry(ip=m.group(1), mac=m.group(2), interface=m.group(3).strip())
                )
        return entries

    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]:
        output = await client.execute("show lldp remote-device all")
        neighbors = []
        local_port = None
        chassis_id = None
        port_id = None
        system_name = None
        for line in output.splitlines():
            m = re.match(r"Local Interface:\s*(\S+)", line.strip())
            if m:
                if local_port and system_name and port_id:
                    neighbors.append(
                        LLDPNeighbor(
                            local_port=local_port,
                            remote_device=system_name,
                            remote_port=port_id,
                            remote_chassis_id=chassis_id,
                        )
                    )
                local_port = m.group(1)
                chassis_id = None
                port_id = None
                system_name = None
                continue
            m = re.match(r"Chassis ID:\s*(\S+)", line.strip())
            if m:
                chassis_id = m.group(1)
            m = re.match(r"Port ID:\s*(\S+)", line.strip())
            if m:
                port_id = m.group(1)
            m = re.match(r"System Name:\s*(.+)", line.strip())
            if m:
                system_name = m.group(1).strip()
        if local_port and system_name and port_id:
            neighbors.append(
                LLDPNeighbor(
                    local_port=local_port,
                    remote_device=system_name,
                    remote_port=port_id,
                    remote_chassis_id=chassis_id,
                )
            )
        return neighbors

    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]:
        output = await client.execute("show interfaces status all")
        interfaces = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+\S*\s+\S+\s+(Up|Down)\s",
                line.strip(),
            )
            if m and not line.strip().startswith(("Port", "---")):
                speed_match = re.search(r"(\d+)\s+(Full|Half)", line)
                speed = f"{speed_match.group(1)}M" if speed_match else None
                interfaces.append(
                    InterfaceDetail(
                        name=m.group(1),
                        status=m.group(2).lower(),
                        speed=speed,
                    )
                )
        return interfaces

    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]:
        output = await client.execute("show vlan brief")
        vlans = []
        for line in output.splitlines():
            m = re.match(r"(\d+)\s+(\S+(?:\s+\S+)*?)\s{2,}\S+", line.strip())
            if m and not line.strip().startswith(("VLAN", "---")):
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
            m = re.match(r"System Name\.+\s*(.+)", line)
            if m:
                hostname = m.group(1).strip()
            m = re.match(r"Machine Model\.+\s*(.+)", line)
            if m:
                model = m.group(1).strip()
            m = re.match(r"Serial Number\.+\s*(.+)", line)
            if m:
                serial = m.group(1).strip()
            m = re.match(r"Software Version\.+\s*(.+)", line)
            if m:
                firmware = m.group(1).strip()
        return DeviceInfo(
            hostname=hostname, model=model, serial=serial, firmware=firmware
        )
