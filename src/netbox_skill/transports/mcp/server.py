"""MCP server entry point — registers all tools and starts the server."""

from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from netbox_skill.clients.netbox import NetBoxClient
from netbox_skill.config import load_config
from netbox_skill.models.common import CredentialSet, DeviceTarget
from netbox_skill.services.discovery import DiscoveryService
from netbox_skill.services.netbox import NetBoxService
from netbox_skill.services.orchestrator import OrchestratorService
from netbox_skill.services.rack_vision import RackVisionService
from netbox_skill.transports.mcp import tools_discovery, tools_netbox, tools_orchestrator, tools_rack
from netbox_skill.vision.claude import ClaudeVisionProvider


class DefaultCredentialResolver:
    def __init__(self, config):
        self._config = config

    async def resolve(self, target: DeviceTarget) -> CredentialSet:
        if target.credentials:
            return target.credentials
        if target.host in self._config.device_overrides:
            override = self._config.device_overrides[target.host]
            return CredentialSet(
                username=override.get("username", self._config.default_ssh_username or "admin"),
                password=override.get("password", self._config.default_ssh_password),
                ssh_key_path=override.get("ssh_key", self._config.default_ssh_key_path),
            )
        return CredentialSet(
            username=self._config.default_ssh_username or "admin",
            password=self._config.default_ssh_password,
            ssh_key_path=self._config.default_ssh_key_path,
        )


def create_server() -> Server:
    config = load_config()
    server = Server("netbox-skill")

    netbox_client = NetBoxClient(
        url=config.netbox_url,
        token=config.netbox_token,
        verify_ssl=config.netbox_verify_ssl,
    )
    netbox_service = NetBoxService(client=netbox_client)

    cred_resolver = DefaultCredentialResolver(config)
    discovery_service = DiscoveryService(
        credential_resolver=cred_resolver,
        max_concurrent=config.max_concurrent_sessions,
    )

    orchestrator_service = OrchestratorService(
        netbox=netbox_service, discovery=discovery_service
    )

    vision_provider = None
    rack_vision_service = None
    if config.anthropic_api_key:
        vision_provider = ClaudeVisionProvider(
            api_key=config.anthropic_api_key, model=config.vision_model
        )
        rack_vision_service = RackVisionService(
            vision=vision_provider,
            netbox=netbox_service,
            confidence_threshold=config.vision_confidence_threshold,
        )

    # Collect all tools from all modules
    all_tools: list[Tool] = []
    all_tools.extend(tools_netbox.get_tools())
    all_tools.extend(tools_discovery.get_tools())
    all_tools.extend(tools_orchestrator.get_tools())
    if rack_vision_service:
        all_tools.extend(tools_rack.get_tools())

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return all_tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            result = await tools_netbox.dispatch(name, arguments, netbox_service)
            if result is None:
                result = await tools_discovery.dispatch(name, arguments, discovery_service)
            if result is None:
                result = await tools_orchestrator.dispatch(name, arguments, orchestrator_service)
            if result is None and rack_vision_service:
                result = await tools_rack.dispatch(name, arguments, rack_vision_service)
            if result is None:
                result = {"error": f"Unknown tool: {name}"}
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return server


async def amain():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    import asyncio
    asyncio.run(amain())


if __name__ == "__main__":
    main()
