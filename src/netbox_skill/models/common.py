"""Shared types used across the service."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class CredentialSet(BaseModel):
    username: str
    password: str | None = None
    ssh_key_path: str | None = None


class DeviceTarget(BaseModel):
    host: str
    platform: str
    credentials: CredentialSet | None = None
    device_id: int | None = None


class SyncMode(str, Enum):
    DRY_RUN = "dry_run"
    AUTO = "auto"
    CONFIRM = "confirm"


class ChangeRecord(BaseModel):
    object_type: str
    object_id: int | None = None
    action: str
    detail: dict[str, Any] = {}


class ConflictRecord(BaseModel):
    object_type: str
    field: str
    netbox_value: Any
    discovered_value: Any


class SyncReport(BaseModel):
    device: DeviceTarget
    created: list[ChangeRecord] = []
    updated: list[ChangeRecord] = []
    unchanged: list[str] = []
    conflicts: list[ConflictRecord] = []
    errors: list[str] = []


class BulkResult(BaseModel):
    created: int
    updated: int
    unchanged: int
    errors: list[str] = []
