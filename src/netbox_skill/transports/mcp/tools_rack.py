"""MCP tool definitions for rack photo population."""

from __future__ import annotations

import base64
from typing import Any

from mcp.types import Tool

from netbox_skill.models.common import SyncMode
from netbox_skill.models.rack_vision import DeviceConfirmation, RackContext
from netbox_skill.services.rack_vision import RackVisionService

# Module-level state for multi-step rack workflow
_current_analysis = None


def get_tools() -> list[Tool]:
    return [
        Tool(name="rack_analyze_photo", description="Analyze a rack photo to detect devices and their positions", inputSchema={"type": "object", "properties": {"image_base64": {"type": "string", "description": "Base64-encoded rack photo"}, "rack_id": {"type": "integer"}, "site": {"type": "string"}, "expected_devices": {"type": "array", "items": {"type": "string"}}}, "required": ["image_base64"]}),
        Tool(name="rack_get_uncertain", description="Get devices that need user confirmation from the last analysis", inputSchema={"type": "object", "properties": {}}),
        Tool(name="rack_confirm_device", description="Confirm or correct a detected device", inputSchema={"type": "object", "properties": {"index": {"type": "integer"}, "confirmed": {"type": "boolean"}, "corrected_model": {"type": "string"}, "device_type_id": {"type": "integer"}, "create_new_type": {"type": "boolean"}}, "required": ["index", "confirmed"]}),
        Tool(name="rack_populate", description="Push confirmed devices into NetBox", inputSchema={"type": "object", "properties": {"rack_id": {"type": "integer"}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["rack_id"]}),
    ]


async def dispatch(name: str, args: dict[str, Any], rack_vision: RackVisionService) -> Any:
    global _current_analysis

    if name == "rack_analyze_photo":
        image = base64.b64decode(args["image_base64"])
        context = RackContext(
            rack_id=args.get("rack_id"),
            site=args.get("site"),
            expected_devices=args.get("expected_devices"),
        )
        _current_analysis = await rack_vision.analyze_rack_photo(image, context)
        _current_analysis = await rack_vision.match_device_types(_current_analysis)
        devices = [d.model_dump() for d in _current_analysis.devices]
        return {"devices": devices, "total": len(devices)}

    if name == "rack_get_uncertain":
        if not _current_analysis:
            return {"error": "No analysis available. Run rack_analyze_photo first."}
        uncertain = rack_vision.get_uncertain_devices(_current_analysis)
        return [
            {"index": idx, "device": dev.model_dump(), "crop_base64": base64.b64encode(crop).decode()}
            for idx, dev, crop in uncertain
        ]

    if name == "rack_confirm_device":
        if not _current_analysis:
            return {"error": "No analysis available."}
        conf = DeviceConfirmation(**args)
        _current_analysis = rack_vision.apply_confirmations(_current_analysis, [conf])
        return {"status": "confirmed", "device": _current_analysis.devices[args["index"]].model_dump()}

    if name == "rack_populate":
        if not _current_analysis:
            return {"error": "No analysis available."}
        mode = SyncMode(args.get("mode", "dry_run"))
        report = await rack_vision.populate_rack(_current_analysis, args["rack_id"], mode)
        return report.model_dump()

    return None
