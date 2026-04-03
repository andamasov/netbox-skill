"""MCP tool definitions for orchestration (sync) workflows."""

from __future__ import annotations

from typing import Any

from mcp.types import Tool

from netbox_skill.models.common import DeviceTarget, SyncMode
from netbox_skill.services.orchestrator import OrchestratorService


def get_tools() -> list[Tool]:
    return [
        Tool(name="sync_device", description="Discover a device and sync to NetBox", inputSchema={"type": "object", "properties": {"host": {"type": "string"}, "platform": {"type": "string"}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["host", "platform"]}),
        Tool(name="sync_devices", description="Sync multiple devices to NetBox", inputSchema={"type": "object", "properties": {"targets": {"type": "array", "items": {"type": "object", "properties": {"host": {"type": "string"}, "platform": {"type": "string"}}, "required": ["host", "platform"]}}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["targets"]}),
        Tool(name="sync_topology", description="Sync LLDP-based topology to NetBox cables", inputSchema={"type": "object", "properties": {"targets": {"type": "array", "items": {"type": "object"}}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["targets"]}),
    ]


async def dispatch(name: str, args: dict[str, Any], orchestrator: OrchestratorService) -> Any:
    mode = SyncMode(args.get("mode", "dry_run"))
    if name == "sync_device":
        target = DeviceTarget(host=args["host"], platform=args["platform"])
        report = await orchestrator.sync_device(target, mode)
        return report.model_dump()
    if name == "sync_devices":
        targets = [DeviceTarget(**t) for t in args["targets"]]
        reports = await orchestrator.sync_devices(targets, mode)
        return [r.model_dump() for r in reports]
    if name == "sync_topology":
        targets = [DeviceTarget(**t) for t in args["targets"]]
        report = await orchestrator.sync_topology(targets, mode)
        return report.model_dump()
    return None
