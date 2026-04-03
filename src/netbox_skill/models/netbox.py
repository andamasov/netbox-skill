# src/netbox_skill/models/netbox.py
"""Pydantic models for NetBox API objects."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class NestedObject(BaseModel):
    """Brief nested representation of a related object."""
    model_config = ConfigDict(extra="allow")

    id: int
    url: str | None = None
    display: str | None = None
    name: str | None = None
    slug: str | None = None


class ChoiceField(BaseModel):
    value: str
    label: str


# --- Read Models (from API responses) ---


class Device(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str | None = None
    status: ChoiceField | None = None
    site: NestedObject | None = None
    location: NestedObject | None = None
    rack: NestedObject | None = None
    position: float | None = None
    face: ChoiceField | None = None
    device_type: NestedObject | dict | None = None
    role: NestedObject | None = None
    platform: NestedObject | None = None
    serial: str | None = None
    asset_tag: str | None = None
    primary_ip4: NestedObject | dict | None = None
    primary_ip6: NestedObject | dict | None = None
    custom_fields: dict[str, Any] = {}
    tags: list[NestedObject] = []
    created: str | None = None
    last_updated: str | None = None


class Interface(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str
    device: NestedObject | None = None
    type: ChoiceField | None = None
    enabled: bool = True
    mtu: int | None = None
    speed: int | None = None
    description: str | None = None
    mac_address: str | None = None
    mode: ChoiceField | None = None
    untagged_vlan: NestedObject | None = None
    tagged_vlans: list[NestedObject] = []
    custom_fields: dict[str, Any] = {}
    tags: list[NestedObject] = []


class IPAddress(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    address: str
    status: ChoiceField | None = None
    assigned_object_type: str | None = None
    assigned_object_id: int | None = None
    assigned_object: dict | None = None
    dns_name: str | None = None
    custom_fields: dict[str, Any] = {}
    tags: list[NestedObject] = []


class Prefix(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    prefix: str
    status: ChoiceField | None = None
    site: NestedObject | None = None
    vlan: NestedObject | None = None
    role: NestedObject | None = None
    custom_fields: dict[str, Any] = {}


class VLAN(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    vid: int
    name: str
    status: ChoiceField | None = None
    site: NestedObject | None = None
    group: NestedObject | None = None
    role: NestedObject | None = None
    custom_fields: dict[str, Any] = {}


class Cable(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    a_terminations: list[dict[str, Any]] = []
    b_terminations: list[dict[str, Any]] = []
    status: ChoiceField | None = None
    type: str | None = None
    label: str | None = None
    length: float | None = None
    length_unit: ChoiceField | None = None


class Site(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str
    slug: str
    status: ChoiceField | None = None
    region: NestedObject | None = None
    custom_fields: dict[str, Any] = {}


class Location(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str
    slug: str
    site: NestedObject | None = None


class Rack(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str
    site: NestedObject | None = None
    location: NestedObject | None = None
    status: ChoiceField | None = None
    u_height: int = 42
    custom_fields: dict[str, Any] = {}


class DeviceType(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    manufacturer: NestedObject | None = None
    model: str
    slug: str
    u_height: float = 1
    custom_fields: dict[str, Any] = {}


class Manufacturer(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str
    slug: str


class Platform(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str
    slug: str
    manufacturer: NestedObject | None = None


class DeviceRole(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    url: str
    display: str
    name: str
    slug: str
    color: str | None = None


# --- Create Models (for POST) ---


class DeviceCreate(BaseModel):
    name: str
    role: int
    device_type: int
    site: int
    status: str = "active"
    location: int | None = None
    rack: int | None = None
    position: float | None = None
    face: str | None = None
    platform: int | None = None
    serial: str | None = None
    asset_tag: str | None = None
    custom_fields: dict[str, Any] | None = None
    tags: list[dict[str, Any]] | None = None


class InterfaceCreate(BaseModel):
    device: int
    name: str
    type: str = "other"
    enabled: bool = True
    mtu: int | None = None
    speed: int | None = None
    description: str | None = None
    mac_address: str | None = None
    mode: str | None = None


class IPAddressCreate(BaseModel):
    address: str
    status: str = "active"
    assigned_object_type: str | None = None
    assigned_object_id: int | None = None
    dns_name: str | None = None


class CableCreate(BaseModel):
    a_terminations: list[dict[str, Any]]
    b_terminations: list[dict[str, Any]]
    status: str | None = None
    type: str | None = None
    label: str | None = None


# --- Update Models (for PATCH, all fields optional) ---


class DeviceUpdate(BaseModel):
    name: str | None = None
    role: int | None = None
    device_type: int | None = None
    site: int | None = None
    status: str | None = None
    location: int | None = None
    rack: int | None = None
    position: float | None = None
    face: str | None = None
    platform: int | None = None
    serial: str | None = None
    asset_tag: str | None = None
    custom_fields: dict[str, Any] | None = None
