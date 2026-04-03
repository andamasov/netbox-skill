"""MCP tool definitions for device discovery."""

from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from netbox_skill.models.common import CredentialSet, DeviceTarget
from netbox_skill.services.discovery import DiscoveryService


def register_discovery_tools(server: Server, discovery: DiscoveryService) -> None:

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="discovery_device", description="Discover data from a single device via SSH", inputSchema={"type": "object", "properties": {"host": {"type": "string"}, "platform": {"type": "string"}, "username": {"type": "string"}, "password": {"type": "string"}, "data_types": {"type": "array", "items": {"type": "string"}, "description": "Optional filter: mac_table, arp_table, lldp, interfaces, vlans, device_info"}}, "required": ["host", "platform"]}),
            Tool(name="discovery_devices", description="Discover data from multiple devices", inputSchema={"type": "object", "properties": {"targets": {"type": "array", "items": {"type": "object", "properties": {"host": {"type": "string"}, "platform": {"type": "string"}}, "required": ["host", "platform"]}}, "data_types": {"type": "array", "items": {"type": "string"}}}, "required": ["targets"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            result = await _dispatch(name, arguments, discovery)
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _dispatch(name: str, args: dict[str, Any], discovery: DiscoveryService) -> Any:
    if name == "discovery_device":
        creds = None
        if args.get("username"):
            creds = CredentialSet(username=args["username"], password=args.get("password"))
        target = DeviceTarget(host=args["host"], platform=args["platform"], credentials=creds)
        result = await discovery.discover_device(target, data_types=args.get("data_types"))
        return result.model_dump()
    if name == "discovery_devices":
        targets = [DeviceTarget(**t) for t in args["targets"]]
        results = await discovery.discover_devices(targets, data_types=args.get("data_types"))
        return [r.model_dump() for r in results]
    return {"error": f"Unknown tool: {name}"}
