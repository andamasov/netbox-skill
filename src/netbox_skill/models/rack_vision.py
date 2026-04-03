# src/netbox_skill/models/rack_vision.py
"""Models for the rack photo population feature."""

from __future__ import annotations

from pydantic import BaseModel

from netbox_skill.models.common import ChangeRecord


class RackContext(BaseModel):
    rack_id: int | None = None
    site: str | None = None
    expected_devices: list[str] | None = None


class DeviceTypeMatch(BaseModel):
    device_type_id: int
    name: str
    similarity: float


class DetectedDevice(BaseModel):
    u_start: int | None = None
    u_end: int | None = None
    mount_type: str  # "rack" or "shelf"
    model_guess: str
    confidence: float
    asset_tag: str | None = None
    serial: str | None = None
    hostname_label: str | None = None
    crop_region: tuple[int, int, int, int]
    matched_device_type_id: int | None = None
    match_candidates: list[DeviceTypeMatch] | None = None


class RackAnalysis(BaseModel):
    devices: list[DetectedDevice]
    annotated_image: bytes
    rack_context: RackContext
    errors: list[str] = []


class DeviceConfirmation(BaseModel):
    index: int
    confirmed: bool
    corrected_model: str | None = None
    corrected_mount_type: str | None = None
    corrected_u_start: int | None = None
    corrected_u_end: int | None = None
    corrected_asset_tag: str | None = None
    corrected_serial: str | None = None
    device_type_id: int | None = None
    create_new_type: bool = False


class RackPopulationReport(BaseModel):
    rack_id: int
    created: list[ChangeRecord] = []
    updated: list[ChangeRecord] = []
    skipped: list[str] = []
    errors: list[str] = []
