"""MCP server entry point — registers all tools and starts the server."""

from __future__ import annotations

from mcp.server import Server
from mcp.server.stdio import stdio_server

from netbox_skill.clients.netbox import NetBoxClient
from netbox_skill.config import load_config
from netbox_skill.services.discovery import DiscoveryService
from netbox_skill.services.netbox import NetBoxService
from netbox_skill.services.orchestrator import OrchestratorService
from netbox_skill.services.rack_vision import RackVisionService
from netbox_skill.vision.claude import ClaudeVisionProvider
from netbox_skill.models.common import CredentialSet, DeviceTarget

from netbox_skill.transports.mcp.tools_netbox import register_netbox_tools
from netbox_skill.transports.mcp.tools_discovery import register_discovery_tools
from netbox_skill.transports.mcp.tools_orchestrator import register_orchestrator_tools
from netbox_skill.transports.mcp.tools_rack import register_rack_tools


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

    register_netbox_tools(server, netbox_service)
    register_discovery_tools(server, discovery_service)
    register_orchestrator_tools(server, orchestrator_service)
    if rack_vision_service:
        register_rack_tools(server, rack_vision_service)

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
