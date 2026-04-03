"""MCP tool definitions for NetBox CRUD operations."""

from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from netbox_skill.models.netbox import DeviceCreate, DeviceUpdate
from netbox_skill.services.netbox import NetBoxService


def register_netbox_tools(server: Server, netbox: NetBoxService) -> None:

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="netbox_status", description="Get NetBox instance status", inputSchema={"type": "object", "properties": {}}),
            Tool(name="netbox_get_devices", description="List devices with optional filters", inputSchema={"type": "object", "properties": {"filters": {"type": "object", "description": "Filter parameters (e.g., status, site, role, name)"}}}),
            Tool(name="netbox_create_device", description="Create a device in NetBox", inputSchema={"type": "object", "properties": {"name": {"type": "string"}, "role": {"type": "integer"}, "device_type": {"type": "integer"}, "site": {"type": "integer"}, "status": {"type": "string"}, "serial": {"type": "string"}, "rack": {"type": "integer"}, "position": {"type": "number"}}, "required": ["name", "role", "device_type", "site"]}),
            Tool(name="netbox_update_device", description="Update a device in NetBox", inputSchema={"type": "object", "properties": {"id": {"type": "integer"}, "data": {"type": "object"}}, "required": ["id", "data"]}),
            Tool(name="netbox_delete_device", description="Delete a device from NetBox", inputSchema={"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}),
            Tool(name="netbox_search", description="Search any NetBox endpoint with filters", inputSchema={"type": "object", "properties": {"endpoint": {"type": "string", "description": "API endpoint (e.g., dcim/devices/, ipam/ip-addresses/)"}, "filters": {"type": "object"}}, "required": ["endpoint"]}),
            Tool(name="netbox_get_interfaces", description="List interfaces with optional filters", inputSchema={"type": "object", "properties": {"filters": {"type": "object"}}}),
            Tool(name="netbox_get_ip_addresses", description="List IP addresses with optional filters", inputSchema={"type": "object", "properties": {"filters": {"type": "object"}}}),
            Tool(name="netbox_get_vlans", description="List VLANs with optional filters", inputSchema={"type": "object", "properties": {"filters": {"type": "object"}}}),
            Tool(name="netbox_get_sites", description="List sites", inputSchema={"type": "object", "properties": {"filters": {"type": "object"}}}),
            Tool(name="netbox_get_racks", description="List racks with optional filters", inputSchema={"type": "object", "properties": {"filters": {"type": "object"}}}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            result = await _dispatch(name, arguments, netbox)
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _dispatch(name: str, args: dict[str, Any], netbox: NetBoxService) -> Any:
    if name == "netbox_status":
        return await netbox._client.status()
    if name == "netbox_get_devices":
        devices = await netbox.get_devices(**(args.get("filters") or {}))
        return [d.model_dump() for d in devices]
    if name == "netbox_create_device":
        data = DeviceCreate(**args)
        device = await netbox.create_device(data)
        return device.model_dump()
    if name == "netbox_update_device":
        data = DeviceUpdate(**args["data"])
        device = await netbox.update_device(args["id"], data)
        return device.model_dump()
    if name == "netbox_delete_device":
        await netbox.delete_device(args["id"])
        return {"status": "deleted"}
    if name == "netbox_search":
        results = await netbox._client.get_all(args["endpoint"], params=args.get("filters"))
        return results
    if name == "netbox_get_interfaces":
        ifaces = await netbox.get_interfaces(**(args.get("filters") or {}))
        return [i.model_dump() for i in ifaces]
    if name == "netbox_get_ip_addresses":
        ips = await netbox.get_ip_addresses(**(args.get("filters") or {}))
        return [ip.model_dump() for ip in ips]
    if name == "netbox_get_vlans":
        vlans = await netbox.get_vlans(**(args.get("filters") or {}))
        return [v.model_dump() for v in vlans]
    if name == "netbox_get_sites":
        sites = await netbox.get_sites(**(args.get("filters") or {}))
        return [s.model_dump() for s in sites]
    if name == "netbox_get_racks":
        racks = await netbox.get_racks(**(args.get("filters") or {}))
        return [r.model_dump() for r in racks]
    return {"error": f"Unknown tool: {name}"}
