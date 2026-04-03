# src/netbox_skill/models/discovery.py
"""Models for data collected from network devices via SSH/CLI."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from netbox_skill.models.common import DeviceTarget


class MACEntry(BaseModel):
    mac: str
    port: str
    vlan: int | None = None


class ARPEntry(BaseModel):
    ip: str
    mac: str
    interface: str


class LLDPNeighbor(BaseModel):
    local_port: str
    remote_device: str
    remote_port: str
    remote_chassis_id: str | None = None


class InterfaceDetail(BaseModel):
    name: str
    status: str
    speed: str | None = None
    mtu: int | None = None
    description: str | None = None
    vlans: list[int] = []


class VLANInfo(BaseModel):
    id: int
    name: str
    ports: list[str] = []


class DeviceInfo(BaseModel):
    hostname: str
    model: str | None = None
    serial: str | None = None
    firmware: str | None = None


class DiscoveryResult(BaseModel):
    target: DeviceTarget
    device_info: DeviceInfo | None = None
    mac_table: list[MACEntry] = []
    arp_table: list[ARPEntry] = []
    lldp_neighbors: list[LLDPNeighbor] = []
    interfaces: list[InterfaceDetail] = []
    vlans: list[VLANInfo] = []
    errors: list[str] = []
    timestamp: datetime
