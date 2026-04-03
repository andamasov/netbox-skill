# NetBox Skill — Design Specification

**Date:** 2026-04-02
**Status:** Draft
**Target:** NetBox Community v4.5.6 (Docker 4.0.2)

## Overview

A full-featured Python service for NetBox integration and network device discovery. The service provides two functional domains — NetBox API operations and SSH-based device discovery — combined with orchestration workflows that discover network topology and populate NetBox. The architecture is transport-agnostic: an MCP server is the primary interface, with an HTTP/REST API entry point scaffolded for future use.

## Architecture

```
Transport Layer
  MCP Server  |  HTTP/FastAPI (future)
        |              |
Service Layer (async, transport-agnostic)
  NetBoxService  |  DiscoveryService  |  OrchestratorService
        |              |
Client/Parser Layer
  NetBoxClient (httpx)  |  SSHClient (asyncssh)  |  DeviceParsers (pluggable)
        |
Models Layer (Pydantic v2)
  NetBox models  |  Discovery models  |  Common types
```

**Language:** Python
**Async throughout:** asyncio + asyncssh for SSH, httpx for HTTP, FastAPI for the HTTP transport.
**Deployment:** Library core with separate entry points — MCP server subprocess and standalone HTTP server can run independently.

## Project Structure

```
netbox-skill/
  src/netbox_skill/
    __init__.py
    config.py
    models/
      __init__.py
      netbox.py
      discovery.py
      common.py
    clients/
      __init__.py
      netbox.py
      ssh.py
    parsers/
      __init__.py
      registry.py
      netgear.py
      fs_com.py
      sonic.py
    services/
      __init__.py
      netbox.py
      discovery.py
      orchestrator.py
    transports/
      __init__.py
      mcp/
        __init__.py
        server.py
        tools_netbox.py
        tools_discovery.py
        tools_orchestrator.py
      http/
        __init__.py
        app.py
        routes_netbox.py
        routes_discovery.py
        routes_orchestrator.py
  tests/
    fixtures/
      netgear/
      fs_com/
      sonic/
    unit/
      parsers/
      services/
      clients/
    integration/
  pyproject.toml
```

## Models

### NetBox Models (`models/netbox.py`)

Pydantic v2 models representing NetBox objects. Focused on fields needed for CRUD and discovery workflows, not exhaustive mirrors. All use `model_config = ConfigDict(extra="allow")` so unknown fields pass through.

Key models: `Device`, `DeviceCreate`, `DeviceUpdate`, `Interface`, `InterfaceCreate`, `IPAddress`, `IPAddressCreate`, `Prefix`, `VLAN`, `Cable`, `CableCreate`, `Site`, `Location`, `Rack`, `DeviceType`, `Manufacturer`, `Platform`, `DeviceRole`.

Each resource has up to three model variants:
- Read model (full object as returned by API)
- Create model (required + optional fields for POST)
- Update model (all fields optional for PATCH)

### Discovery Models (`models/discovery.py`)

Represent raw data collected from devices:

- `MACEntry(mac: str, port: str, vlan: int | None)`
- `ARPEntry(ip: str, mac: str, interface: str)`
- `LLDPNeighbor(local_port: str, remote_device: str, remote_port: str, remote_chassis_id: str | None)`
- `InterfaceDetail(name: str, status: str, speed: str | None, mtu: int | None, description: str | None, vlans: list[int])`
- `VLANInfo(id: int, name: str, ports: list[str])`
- `DeviceInfo(hostname: str, model: str | None, serial: str | None, firmware: str | None)`
- `DiscoveryResult(target: DeviceTarget, device_info: DeviceInfo | None, mac_table: list[MACEntry], arp_table: list[ARPEntry], lldp_neighbors: list[LLDPNeighbor], interfaces: list[InterfaceDetail], vlans: list[VLANInfo], errors: list[str], timestamp: datetime)`

### Common Types (`models/common.py`)

- `CredentialSet(username: str, password: str | None, ssh_key_path: str | None)`
- `DeviceTarget(host: str, platform: str, credentials: CredentialSet | None, device_id: int | None)` — `device_id` is the NetBox ID if the device came from NetBox
- `SyncMode` enum: `dry_run`, `auto`, `confirm`
- `ChangeRecord(object_type: str, object_id: int | None, action: str, detail: dict)`
- `ConflictRecord(object_type: str, field: str, netbox_value: Any, discovered_value: Any)`
- `SyncReport(device: DeviceTarget, created: list[ChangeRecord], updated: list[ChangeRecord], unchanged: list[str], conflicts: list[ConflictRecord], errors: list[str])`
- `BulkResult(created: int, updated: int, unchanged: int, errors: list[str])`

## Clients

### NetBox Client (`clients/netbox.py`)

Async HTTP client wrapping the NetBox REST API using `httpx.AsyncClient`.

```python
class NetBoxClient:
    def __init__(self, url: str, token: str, verify_ssl: bool = True)
```

**Raw methods:**
- `get(endpoint: str, params: dict | None) -> dict`
- `get_all(endpoint: str, params: dict | None) -> list[dict]` — auto-paginates by following `next` URLs, configurable page size (default 100)
- `create(endpoint: str, data: dict | list[dict]) -> dict | list[dict]` — single or bulk
- `update(endpoint: str, id: int, data: dict, partial: bool = True) -> dict` — PATCH by default
- `delete(endpoint: str, id: int) -> None`
- `status() -> dict`

**Typed convenience methods** per resource (delegates to raw methods, handles Pydantic serialization/deserialization):
- `get_devices(**filters) -> list[Device]`
- `create_device(data: DeviceCreate) -> Device`
- `update_device(id: int, data: DeviceUpdate) -> Device`
- `delete_device(id: int) -> None`
- Same pattern for: interfaces, ip_addresses, prefixes, vlans, cables, sites, locations, racks, device_types, manufacturers, platforms, device_roles

### SSH Client (`clients/ssh.py`)

Async SSH client using `asyncssh`.

```python
class SSHClient:
    def __init__(self, host: str, credentials: CredentialSet, timeout: int = 30)
```

**Methods:**
- `connect() -> None`
- `execute(command: str) -> str` — returns raw output
- `execute_commands(commands: list[str]) -> list[str]`
- `close() -> None`
- Async context manager: `async with SSHClient(...) as client:`

Returns raw string output only. No parsing.

## Parsers

### Base Class and Registry (`parsers/registry.py`)

```python
class DeviceParser(ABC):
    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]
    async def get_arp_table(self, client: SSHClient) -> list[ARPEntry]
    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]
    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]
    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]
    async def get_device_info(self, client: SSHClient) -> DeviceInfo
```

Registry via decorator:

```python
PARSER_REGISTRY: dict[str, type[DeviceParser]] = {}

@register_parser("netgear")
class NetgearParser(DeviceParser): ...

def get_parser(platform: str) -> DeviceParser:
    """Raises UnknownPlatformError if not found."""
```

Platform strings match NetBox `platform` field values.

### Vendor Parsers

**Netgear** (`parsers/netgear.py`):
- `show mac-address-table`
- `show arp`
- `show lldp remote-device all`
- `show interfaces status all`
- `show vlan brief`
- `show version`

**FS.com** (`parsers/fs_com.py`):
- `show mac address-table`
- `show arp`
- `show lldp neighbors`
- `show interface status`
- `show vlan`
- `show version`

**SONiC** (`parsers/sonic.py`):
- `show mac`
- `show arp`
- `show lldp table`
- `show interfaces status`
- `show vlan brief`
- `show platform summary`

All parsing via regex. No TextFSM/NTC-Templates dependency initially.

**Adding a new vendor:** Create file, subclass `DeviceParser`, implement 6 methods, decorate with `@register_parser("platform_name")`. No other files change.

## Services

### NetBox Service (`services/netbox.py`)

```python
class NetBoxService:
    def __init__(self, client: NetBoxClient)
```

**CRUD pass-throughs** for all resource types with Pydantic validation.

**Higher-level operations:**
- `find_or_create_device(data) -> (Device, bool)` — search by name/serial, create if missing
- `find_or_create_interface(device_id, name) -> (Interface, bool)`
- `assign_ip_to_interface(ip, interface_id) -> IPAddress`
- `create_cable_between(a_type, a_id, b_type, b_id) -> Cable` — with duplicate check
- `get_device_with_interfaces(device_id) -> dict`
- `bulk_create_or_update(endpoint, items, match_fields) -> BulkResult` — generic upsert: match by specified fields, create missing, update changed

### Discovery Service (`services/discovery.py`)

```python
class DiscoveryService:
    def __init__(self, credential_resolver: CredentialResolver, max_concurrent: int = 10)
```

**`CredentialResolver`** — protocol class. Resolves credentials for a device target using priority chain: per-request → config file → environment variables → NetBox secrets (if available). Swappable implementation.

**Methods:**
- `discover_device(target: DeviceTarget, data_types: list[str] | None = None) -> DiscoveryResult` — connect to one device, run selected or all parsers
- `discover_devices(targets: list[DeviceTarget], data_types) -> list[DiscoveryResult]` — concurrent with `asyncio.Semaphore(max_concurrent)`
- `discover_from_netbox(netbox: NetBoxService, filters: dict, data_types) -> list[DiscoveryResult]` — pull device list from NetBox by site/role/tag, resolve management IPs, run discovery

`data_types` filter accepts: `"mac_table"`, `"arp_table"`, `"lldp"`, `"interfaces"`, `"vlans"`, `"device_info"`. `None` means all.

### Orchestrator Service (`services/orchestrator.py`)

```python
class OrchestratorService:
    def __init__(self, netbox: NetBoxService, discovery: DiscoveryService)
```

**Methods:**
- `sync_device(target: DeviceTarget, mode: SyncMode) -> SyncReport` — discover, diff against NetBox, apply based on mode
- `sync_devices(targets: list[DeviceTarget], mode: SyncMode) -> list[SyncReport]`
- `sync_topology(targets: list[DeviceTarget], mode: SyncMode) -> SyncReport` — LLDP-based cable/connection sync across devices

**SyncMode behavior:**
- `dry_run` — return diff only, no writes to NetBox
- `auto` — apply all changes automatically
- `confirm` — return diff, apply only explicitly confirmed items (for interactive use via MCP)

## Transports

### MCP Server (`transports/mcp/`)

Entry point: `python -m netbox_skill.transports.mcp`

Tool prefixes and definitions:

**`netbox_*`** — direct NetBox operations:
- `netbox_get_devices`, `netbox_create_device`, `netbox_update_device`, `netbox_delete_device`
- Same pattern for: interfaces, ip_addresses, prefixes, vlans, cables, sites, racks, and other resources
- `netbox_search` — generic search across any endpoint with filters
- `netbox_status` — NetBox instance info

**`discovery_*`** — device querying:
- `discovery_device` — discover one device (host, platform, optional credentials, optional data_types)
- `discovery_devices` — discover multiple
- `discovery_from_netbox` — discover by NetBox filters (site, role, tag)
- `discovery_mac_lookup` — find which port a MAC is on across devices
- `discovery_ip_trace` — trace IP → ARP → MAC → port → switch

**`sync_*`** — orchestration:
- `sync_device` — discover + populate NetBox for one device
- `sync_devices` — bulk
- `sync_topology` — LLDP-based cable sync
- All accept `mode` parameter

### HTTP Server (`transports/http/`)

FastAPI app entry point: `python -m netbox_skill.transports.http`

Route structure mirrors MCP tools:
- `GET/POST/PATCH/DELETE /api/netbox/{resource}/`
- `POST /api/discovery/device`, `POST /api/discovery/devices`
- `POST /api/sync/device`, `POST /api/sync/topology`

**Initial build:** Entry point and route structure scaffolded. Endpoints return 501 Not Implemented. MCP transport is the priority; HTTP routes are filled in as a second phase using the same service calls.

## Configuration

```python
class Config(BaseModel):
    netbox_url: str           # NETBOX_URL
    netbox_token: str         # NETBOX_TOKEN
    netbox_verify_ssl: bool = True  # NETBOX_VERIFY_SSL
    default_ssh_username: str | None = None  # DEVICE_USERNAME
    default_ssh_password: str | None = None  # DEVICE_PASSWORD
    default_ssh_key_path: str | None = None  # DEVICE_SSH_KEY
    max_concurrent_sessions: int = 10  # MAX_CONCURRENT_SESSIONS
    ssh_timeout: int = 30     # SSH_TIMEOUT
    config_file: str | None = None  # CONFIG_FILE
```

Optional YAML config file for device/group-specific overrides:

```yaml
devices:
  "192.168.1.1":
    platform: netgear
    username: admin
    password: secret
groups:
  core-switches:
    platform: sonic
    username: admin
    ssh_key: /path/to/key
```

**Credential resolution priority:** per-request > config file device entry > config file group entry > environment variables > NetBox secrets plugin (if available).

## Error Handling

**Exception hierarchy:**
```
NetBoxSkillError (base)
  NetBoxClientError
    NetBoxAuthError (401/403)
    NetBoxNotFoundError (404)
    NetBoxValidationError (400, includes field-level errors)
    NetBoxServerError (5xx)
  DeviceError
    DeviceConnectionError (SSH failures)
    CommandError (unexpected output)
    UnknownPlatformError (no parser for platform)
  ConfigError (missing/invalid configuration)
```

**Partial failure:** Multi-device operations use `asyncio.gather(return_exceptions=True)`. Individual failures captured in `DiscoveryResult.errors` or `SyncReport.errors`. One device failing does not abort the batch.

## Testing

**Unit tests (`tests/unit/`):**
- **Parsers:** Tested against captured CLI output fixtures in `tests/fixtures/{vendor}/`. One fixture file per command per vendor. Tests verify correct parsing into Pydantic models.
- **Services:** Mocked clients. Test business logic: upsert, diff generation, conflict detection, bulk operations.
- **Clients:** Mocked httpx responses (NetBox client) for pagination, error mapping, serialization.

**Integration tests (`tests/integration/`):**
- **Mock SSH sessions:** asyncssh fake server returning fixture data. Full flow: connect > execute > parse > models.
- **NetBox API tests:** Against test NetBox instance (skipped if no `TEST_NETBOX_URL` env var) or mocked with `respx`.

**Test runner:** pytest + pytest-asyncio.

## Dependencies

```
httpx           # Async HTTP client for NetBox API
asyncssh        # Async SSH client for device connections
pydantic>=2.0   # Data models and validation
mcp[cli]        # MCP SDK for MCP server transport
fastapi         # HTTP transport (scaffolded)
uvicorn         # ASGI server for FastAPI
pyyaml          # Config file parsing
pytest          # Test runner (dev)
pytest-asyncio  # Async test support (dev)
respx           # HTTP mocking (dev)
```

## Out of Scope (Initial Build)

- GraphQL support (NetBox has it, but REST is sufficient)
- NetBox Secrets plugin integration for credential resolution (interface is defined, implementation deferred)
- Full HTTP transport implementation (scaffolded only)
- End-to-end tests against real devices
- TextFSM/NTC-Templates integration (regex parsing first)
- SNMP-based discovery
- Scheduled/periodic discovery runs
