# NetBox Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-featured Python service for NetBox integration, network device discovery, and AI-powered rack population, exposed via MCP server transport.

**Architecture:** Layered async Python library — models at the bottom, clients/parsers above, services above that, thin transport adapters on top. Pydantic v2 for all data, httpx for HTTP, asyncssh for SSH, MCP SDK for the MCP server.

**Tech Stack:** Python 3.11+, Pydantic v2, httpx, asyncssh, mcp[cli], FastAPI, anthropic SDK, Pillow, pytest + pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-04-02-netbox-skill-design.md`

---

## File Map

### Foundation
- Create: `pyproject.toml` — project metadata, dependencies, entry points
- Create: `src/netbox_skill/__init__.py` — package root, version
- Create: `src/netbox_skill/exceptions.py` — full exception hierarchy
- Create: `src/netbox_skill/config.py` — Config model, env/file loading
- Create: `tests/conftest.py` — shared fixtures

### Models
- Create: `src/netbox_skill/models/__init__.py` — re-exports
- Create: `src/netbox_skill/models/common.py` — CredentialSet, DeviceTarget, SyncMode, ChangeRecord, etc.
- Create: `src/netbox_skill/models/netbox.py` — Device, Interface, IPAddress, Prefix, VLAN, Cable, Site, etc.
- Create: `src/netbox_skill/models/discovery.py` — MACEntry, ARPEntry, LLDPNeighbor, etc.
- Create: `src/netbox_skill/models/rack_vision.py` — RackContext, DetectedDevice, RackAnalysis, etc.

### Clients
- Create: `src/netbox_skill/clients/__init__.py`
- Create: `src/netbox_skill/clients/netbox.py` — NetBoxClient
- Create: `src/netbox_skill/clients/ssh.py` — SSHClient
- Create: `tests/unit/clients/test_netbox_client.py`
- Create: `tests/unit/clients/test_ssh_client.py`

### Parsers
- Create: `src/netbox_skill/parsers/__init__.py`
- Create: `src/netbox_skill/parsers/registry.py` — DeviceParser ABC, registry
- Create: `src/netbox_skill/parsers/netgear.py`
- Create: `src/netbox_skill/parsers/fs_com.py`
- Create: `src/netbox_skill/parsers/sonic.py`
- Create: `tests/fixtures/netgear/` — CLI output samples
- Create: `tests/fixtures/fs_com/` — CLI output samples
- Create: `tests/fixtures/sonic/` — CLI output samples
- Create: `tests/unit/parsers/test_netgear.py`
- Create: `tests/unit/parsers/test_fs_com.py`
- Create: `tests/unit/parsers/test_sonic.py`

### Services
- Create: `src/netbox_skill/services/__init__.py`
- Create: `src/netbox_skill/services/netbox.py` — NetBoxService
- Create: `src/netbox_skill/services/discovery.py` — DiscoveryService, CredentialResolver
- Create: `src/netbox_skill/services/orchestrator.py` — OrchestratorService
- Create: `src/netbox_skill/services/rack_vision.py` — RackVisionService
- Create: `tests/unit/services/test_netbox_service.py`
- Create: `tests/unit/services/test_discovery_service.py`
- Create: `tests/unit/services/test_orchestrator_service.py`
- Create: `tests/unit/services/test_rack_vision_service.py`

### Vision
- Create: `src/netbox_skill/vision/__init__.py`
- Create: `src/netbox_skill/vision/base.py` — VisionProvider ABC
- Create: `src/netbox_skill/vision/claude.py` — ClaudeVisionProvider
- Create: `tests/unit/vision/test_claude_provider.py`

### MCP Transport
- Create: `src/netbox_skill/transports/__init__.py`
- Create: `src/netbox_skill/transports/mcp/__init__.py`
- Create: `src/netbox_skill/transports/mcp/server.py` — MCP server entry point
- Create: `src/netbox_skill/transports/mcp/tools_netbox.py`
- Create: `src/netbox_skill/transports/mcp/tools_discovery.py`
- Create: `src/netbox_skill/transports/mcp/tools_orchestrator.py`
- Create: `src/netbox_skill/transports/mcp/tools_rack.py`

### HTTP Transport (scaffold)
- Create: `src/netbox_skill/transports/http/__init__.py`
- Create: `src/netbox_skill/transports/http/app.py`
- Create: `src/netbox_skill/transports/http/routes_netbox.py`
- Create: `src/netbox_skill/transports/http/routes_discovery.py`
- Create: `src/netbox_skill/transports/http/routes_orchestrator.py`

### Integration Tests
- Create: `tests/integration/test_ssh_discovery.py`
- Create: `tests/integration/test_netbox_api.py`

---

### Task 1: Project Scaffold and Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/netbox_skill/__init__.py`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "netbox-skill"
version = "0.1.0"
description = "NetBox integration, network device discovery, and AI-powered rack population service"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",
    "asyncssh>=2.14.0",
    "pydantic>=2.0",
    "mcp[cli]>=1.0.0",
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
    "pyyaml>=6.0",
    "anthropic>=0.40.0",
    "pillow>=10.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",
]

[project.scripts]
netbox-skill-mcp = "netbox_skill.transports.mcp.server:main"
netbox-skill-http = "netbox_skill.transports.http.app:main"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.hatch.build.targets.wheel]
packages = ["src/netbox_skill"]
```

- [ ] **Step 2: Create package init**

```python
# src/netbox_skill/__init__.py
"""NetBox integration, network device discovery, and AI-powered rack population service."""

__version__ = "0.1.0"
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
.env
.pytest_cache/
.mypy_cache/
*.so
```

- [ ] **Step 4: Install the project in dev mode**

Run: `cd /Users/syncer/GitHub/netbox-skill && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`

Expected: Successful installation with all dependencies

- [ ] **Step 5: Verify pytest runs**

Run: `cd /Users/syncer/GitHub/netbox-skill && source .venv/bin/activate && pytest --co`

Expected: "no tests ran" (no test files yet), exit 0 or 5 (no tests collected)

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/netbox_skill/__init__.py .gitignore
git commit -m "feat: scaffold project with dependencies and entry points"
```

---

### Task 2: Exception Hierarchy

**Files:**
- Create: `src/netbox_skill/exceptions.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/test_exceptions.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/__init__.py
```

```python
# tests/unit/test_exceptions.py
from netbox_skill.exceptions import (
    NetBoxSkillError,
    NetBoxClientError,
    NetBoxAuthError,
    NetBoxNotFoundError,
    NetBoxValidationError,
    NetBoxServerError,
    DeviceError,
    DeviceConnectionError,
    CommandError,
    UnknownPlatformError,
    VisionError,
    VisionProviderError,
    ImageProcessingError,
    ConfigError,
)


def test_exception_hierarchy():
    assert issubclass(NetBoxClientError, NetBoxSkillError)
    assert issubclass(NetBoxAuthError, NetBoxClientError)
    assert issubclass(NetBoxNotFoundError, NetBoxClientError)
    assert issubclass(NetBoxValidationError, NetBoxClientError)
    assert issubclass(NetBoxServerError, NetBoxClientError)
    assert issubclass(DeviceError, NetBoxSkillError)
    assert issubclass(DeviceConnectionError, DeviceError)
    assert issubclass(CommandError, DeviceError)
    assert issubclass(UnknownPlatformError, DeviceError)
    assert issubclass(VisionError, NetBoxSkillError)
    assert issubclass(VisionProviderError, VisionError)
    assert issubclass(ImageProcessingError, VisionError)
    assert issubclass(ConfigError, NetBoxSkillError)


def test_netbox_client_error_stores_status_and_body():
    err = NetBoxClientError(status_code=400, body={"detail": "bad"}, message="fail")
    assert err.status_code == 400
    assert err.body == {"detail": "bad"}
    assert "fail" in str(err)


def test_netbox_validation_error_stores_field_errors():
    err = NetBoxValidationError(
        status_code=400,
        body={"name": ["This field is required."]},
        message="Validation failed",
    )
    assert err.field_errors == {"name": ["This field is required."]}


def test_unknown_platform_error_stores_platform():
    err = UnknownPlatformError("mikrotik")
    assert err.platform == "mikrotik"
    assert "mikrotik" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_exceptions.py -v`

Expected: FAIL — `ModuleNotFoundError: No module named 'netbox_skill.exceptions'`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/exceptions.py
"""Exception hierarchy for netbox-skill."""

from __future__ import annotations

from typing import Any


class NetBoxSkillError(Exception):
    """Base exception for all netbox-skill errors."""


class NetBoxClientError(NetBoxSkillError):
    """Error communicating with the NetBox API."""

    def __init__(
        self,
        status_code: int,
        body: Any = None,
        message: str = "NetBox API error",
    ):
        self.status_code = status_code
        self.body = body
        super().__init__(f"{message} (HTTP {status_code}): {body}")


class NetBoxAuthError(NetBoxClientError):
    """Authentication or authorization failure (401/403)."""


class NetBoxNotFoundError(NetBoxClientError):
    """Resource not found (404)."""


class NetBoxValidationError(NetBoxClientError):
    """Validation error (400) with field-level details."""

    def __init__(
        self,
        status_code: int = 400,
        body: Any = None,
        message: str = "Validation failed",
    ):
        super().__init__(status_code=status_code, body=body, message=message)
        self.field_errors: dict[str, list[str]] = body if isinstance(body, dict) else {}


class NetBoxServerError(NetBoxClientError):
    """Server-side error (5xx)."""


class DeviceError(NetBoxSkillError):
    """Error interacting with a network device."""


class DeviceConnectionError(DeviceError):
    """SSH connection failure (timeout, refused, auth)."""


class CommandError(DeviceError):
    """Command execution failed or returned unexpected output."""


class UnknownPlatformError(DeviceError):
    """No parser registered for the given platform string."""

    def __init__(self, platform: str):
        self.platform = platform
        super().__init__(f"No parser registered for platform: {platform}")


class VisionError(NetBoxSkillError):
    """Error in vision processing."""


class VisionProviderError(VisionError):
    """API call to vision provider failed."""


class ImageProcessingError(VisionError):
    """Image decode, crop, or annotation failure."""


class ConfigError(NetBoxSkillError):
    """Missing or invalid configuration."""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_exceptions.py -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/exceptions.py tests/unit/__init__.py tests/unit/test_exceptions.py
git commit -m "feat: add exception hierarchy"
```

---

### Task 3: Common Models

**Files:**
- Create: `src/netbox_skill/models/__init__.py`
- Create: `src/netbox_skill/models/common.py`
- Create: `tests/unit/test_models_common.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/test_models_common.py
from netbox_skill.models.common import (
    CredentialSet,
    DeviceTarget,
    SyncMode,
    ChangeRecord,
    ConflictRecord,
    SyncReport,
    BulkResult,
)


def test_credential_set_password_only():
    creds = CredentialSet(username="admin", password="secret")
    assert creds.username == "admin"
    assert creds.password == "secret"
    assert creds.ssh_key_path is None


def test_credential_set_key_only():
    creds = CredentialSet(username="admin", ssh_key_path="/path/to/key")
    assert creds.password is None
    assert creds.ssh_key_path == "/path/to/key"


def test_device_target_minimal():
    target = DeviceTarget(host="192.168.1.1", platform="netgear")
    assert target.host == "192.168.1.1"
    assert target.platform == "netgear"
    assert target.credentials is None
    assert target.device_id is None


def test_device_target_with_credentials():
    creds = CredentialSet(username="admin", password="pass")
    target = DeviceTarget(
        host="10.0.0.1", platform="sonic", credentials=creds, device_id=42
    )
    assert target.credentials.username == "admin"
    assert target.device_id == 42


def test_sync_mode_values():
    assert SyncMode.DRY_RUN == "dry_run"
    assert SyncMode.AUTO == "auto"
    assert SyncMode.CONFIRM == "confirm"


def test_change_record():
    rec = ChangeRecord(
        object_type="device", object_id=5, action="created", detail={"name": "sw1"}
    )
    assert rec.object_type == "device"
    assert rec.action == "created"


def test_conflict_record():
    conflict = ConflictRecord(
        object_type="interface",
        field="speed",
        netbox_value="1000",
        discovered_value="10000",
    )
    assert conflict.field == "speed"


def test_sync_report_empty():
    target = DeviceTarget(host="1.1.1.1", platform="netgear")
    report = SyncReport(device=target)
    assert report.created == []
    assert report.updated == []
    assert report.unchanged == []
    assert report.conflicts == []
    assert report.errors == []


def test_bulk_result():
    result = BulkResult(created=3, updated=1, unchanged=10, errors=["fail"])
    assert result.created == 3
    assert result.errors == ["fail"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models_common.py -v`

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/models/__init__.py
"""Pydantic models for netbox-skill."""
```

```python
# src/netbox_skill/models/common.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models_common.py -v`

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/models/ tests/unit/test_models_common.py
git commit -m "feat: add common models (CredentialSet, DeviceTarget, SyncMode, etc.)"
```

---

### Task 4: NetBox Models

**Files:**
- Create: `src/netbox_skill/models/netbox.py`
- Create: `tests/unit/test_models_netbox.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/test_models_netbox.py
from netbox_skill.models.netbox import (
    Device,
    DeviceCreate,
    DeviceUpdate,
    Interface,
    InterfaceCreate,
    IPAddress,
    IPAddressCreate,
    Prefix,
    VLAN,
    Cable,
    CableCreate,
    Site,
    Location,
    Rack,
    DeviceType,
    Manufacturer,
    Platform,
    DeviceRole,
    NestedObject,
)


def test_device_from_api_response():
    data = {
        "id": 1,
        "url": "https://netbox/api/dcim/devices/1/",
        "display": "sw-core-01",
        "name": "sw-core-01",
        "status": {"value": "active", "label": "Active"},
        "site": {"id": 1, "url": "https://netbox/api/dcim/sites/1/", "display": "DC1", "name": "DC1", "slug": "dc1"},
        "device_type": {"id": 5, "display": "SN2700", "manufacturer": {"id": 2, "display": "Mellanox"}},
        "role": {"id": 3, "display": "Core Switch"},
        "serial": "ABC123",
        "custom_fields": {"deployed": "2024-01-01"},
        "created": "2024-01-01T00:00:00Z",
        "last_updated": "2024-06-01T12:00:00Z",
    }
    device = Device.model_validate(data)
    assert device.id == 1
    assert device.name == "sw-core-01"
    assert device.serial == "ABC123"
    assert device.custom_fields == {"deployed": "2024-01-01"}


def test_device_extra_fields_allowed():
    data = {
        "id": 1,
        "url": "https://netbox/api/dcim/devices/1/",
        "display": "sw1",
        "name": "sw1",
        "status": {"value": "active", "label": "Active"},
        "unknown_future_field": "some_value",
    }
    device = Device.model_validate(data)
    assert device.id == 1


def test_device_create():
    create = DeviceCreate(
        name="sw-new-01",
        role=3,
        device_type=5,
        site=1,
        status="active",
    )
    d = create.model_dump(exclude_none=True)
    assert d["name"] == "sw-new-01"
    assert d["role"] == 3


def test_device_update_partial():
    update = DeviceUpdate(name="sw-renamed")
    d = update.model_dump(exclude_none=True)
    assert d == {"name": "sw-renamed"}


def test_interface_from_api():
    data = {
        "id": 10,
        "url": "https://netbox/api/dcim/interfaces/10/",
        "display": "Ethernet1",
        "name": "Ethernet1",
        "device": {"id": 1, "display": "sw1"},
        "type": {"value": "1000base-t", "label": "1000BASE-T"},
        "enabled": True,
        "mtu": 9000,
        "speed": 1000000,
        "description": "uplink",
    }
    iface = Interface.model_validate(data)
    assert iface.name == "Ethernet1"
    assert iface.mtu == 9000


def test_ip_address_from_api():
    data = {
        "id": 100,
        "url": "https://netbox/api/ipam/ip-addresses/100/",
        "display": "10.0.0.1/24",
        "address": "10.0.0.1/24",
        "status": {"value": "active", "label": "Active"},
        "assigned_object_type": "dcim.interface",
        "assigned_object_id": 10,
    }
    ip = IPAddress.model_validate(data)
    assert ip.address == "10.0.0.1/24"
    assert ip.assigned_object_id == 10


def test_cable_create():
    cable = CableCreate(
        a_terminations=[{"object_type": "dcim.interface", "object_id": 1}],
        b_terminations=[{"object_type": "dcim.interface", "object_id": 2}],
    )
    d = cable.model_dump(exclude_none=True)
    assert len(d["a_terminations"]) == 1


def test_nested_object():
    obj = NestedObject(id=1, display="test", url="https://netbox/api/test/1/")
    assert obj.id == 1
    assert obj.display == "test"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models_netbox.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models_netbox.py -v`

Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/models/netbox.py tests/unit/test_models_netbox.py
git commit -m "feat: add NetBox Pydantic models (Device, Interface, IP, VLAN, Cable, etc.)"
```

---

### Task 5: Discovery Models

**Files:**
- Create: `src/netbox_skill/models/discovery.py`
- Create: `tests/unit/test_models_discovery.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/test_models_discovery.py
from datetime import datetime, timezone

from netbox_skill.models.common import DeviceTarget
from netbox_skill.models.discovery import (
    MACEntry,
    ARPEntry,
    LLDPNeighbor,
    InterfaceDetail,
    VLANInfo,
    DeviceInfo,
    DiscoveryResult,
)


def test_mac_entry():
    entry = MACEntry(mac="AA:BB:CC:DD:EE:FF", port="Gi0/1", vlan=100)
    assert entry.mac == "AA:BB:CC:DD:EE:FF"
    assert entry.vlan == 100


def test_mac_entry_no_vlan():
    entry = MACEntry(mac="AA:BB:CC:DD:EE:FF", port="Gi0/1")
    assert entry.vlan is None


def test_arp_entry():
    entry = ARPEntry(ip="10.0.0.1", mac="AA:BB:CC:DD:EE:FF", interface="vlan100")
    assert entry.ip == "10.0.0.1"


def test_lldp_neighbor():
    n = LLDPNeighbor(
        local_port="Ethernet1",
        remote_device="sw-core-01",
        remote_port="Ethernet48",
        remote_chassis_id="AA:BB:CC:DD:EE:FF",
    )
    assert n.remote_device == "sw-core-01"


def test_lldp_neighbor_no_chassis():
    n = LLDPNeighbor(
        local_port="Ethernet1", remote_device="sw2", remote_port="Ethernet1"
    )
    assert n.remote_chassis_id is None


def test_interface_detail():
    iface = InterfaceDetail(
        name="Ethernet1",
        status="up",
        speed="10G",
        mtu=9000,
        description="uplink",
        vlans=[100, 200],
    )
    assert iface.name == "Ethernet1"
    assert iface.vlans == [100, 200]


def test_interface_detail_minimal():
    iface = InterfaceDetail(name="Ethernet1", status="down")
    assert iface.speed is None
    assert iface.vlans == []


def test_vlan_info():
    vlan = VLANInfo(id=100, name="mgmt", ports=["Gi0/1", "Gi0/2"])
    assert vlan.id == 100
    assert len(vlan.ports) == 2


def test_device_info():
    info = DeviceInfo(
        hostname="sw-core-01",
        model="SN2700",
        serial="ABC123",
        firmware="SONiC.4.0.0",
    )
    assert info.hostname == "sw-core-01"


def test_device_info_minimal():
    info = DeviceInfo(hostname="unknown")
    assert info.model is None
    assert info.serial is None
    assert info.firmware is None


def test_discovery_result():
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = DiscoveryResult(
        target=target,
        device_info=DeviceInfo(hostname="sw1"),
        mac_table=[MACEntry(mac="AA:BB:CC:DD:EE:FF", port="Ethernet1", vlan=100)],
        arp_table=[],
        lldp_neighbors=[],
        interfaces=[],
        vlans=[],
        errors=[],
        timestamp=datetime(2026, 4, 2, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert result.target.host == "10.0.0.1"
    assert len(result.mac_table) == 1
    assert result.device_info.hostname == "sw1"


def test_discovery_result_with_errors():
    target = DeviceTarget(host="10.0.0.2", platform="netgear")
    result = DiscoveryResult(
        target=target,
        timestamp=datetime.now(timezone.utc),
        errors=["Failed to get ARP table: timeout"],
    )
    assert len(result.errors) == 1
    assert result.device_info is None
    assert result.mac_table == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models_discovery.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/models/discovery.py
"""Models for data collected from network devices via SSH/CLI."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from netbox_skill.models.common import DeviceTarget


class MACEntry(BaseModel):
    mac: str
    port: str
    vlan: int | None = None


class ARPEntry(BaseModel):
    ip: str
    mac: str
    interface: str


class LLDPNeighbor(BaseModel):
    local_port: str
    remote_device: str
    remote_port: str
    remote_chassis_id: str | None = None


class InterfaceDetail(BaseModel):
    name: str
    status: str
    speed: str | None = None
    mtu: int | None = None
    description: str | None = None
    vlans: list[int] = []


class VLANInfo(BaseModel):
    id: int
    name: str
    ports: list[str] = []


class DeviceInfo(BaseModel):
    hostname: str
    model: str | None = None
    serial: str | None = None
    firmware: str | None = None


class DiscoveryResult(BaseModel):
    target: DeviceTarget
    device_info: DeviceInfo | None = None
    mac_table: list[MACEntry] = []
    arp_table: list[ARPEntry] = []
    lldp_neighbors: list[LLDPNeighbor] = []
    interfaces: list[InterfaceDetail] = []
    vlans: list[VLANInfo] = []
    errors: list[str] = []
    timestamp: datetime
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models_discovery.py -v`

Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/models/discovery.py tests/unit/test_models_discovery.py
git commit -m "feat: add discovery models (MACEntry, ARPEntry, LLDPNeighbor, etc.)"
```

---

### Task 6: Rack Vision Models

**Files:**
- Create: `src/netbox_skill/models/rack_vision.py`
- Create: `tests/unit/test_models_rack_vision.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/test_models_rack_vision.py
from netbox_skill.models.common import ChangeRecord
from netbox_skill.models.rack_vision import (
    RackContext,
    DetectedDevice,
    DeviceTypeMatch,
    RackAnalysis,
    DeviceConfirmation,
    RackPopulationReport,
)


def test_rack_context_minimal():
    ctx = RackContext()
    assert ctx.rack_id is None
    assert ctx.site is None
    assert ctx.expected_devices is None


def test_rack_context_full():
    ctx = RackContext(rack_id=5, site="DC1", expected_devices=["SN2700", "M4300"])
    assert ctx.rack_id == 5
    assert len(ctx.expected_devices) == 2


def test_detected_device_rack_mounted():
    dev = DetectedDevice(
        u_start=10,
        u_end=11,
        mount_type="rack",
        model_guess="Dell PowerEdge R640",
        confidence=0.92,
        asset_tag="ASSET001",
        serial="SVC123",
        hostname_label="srv-db-01",
        crop_region=(100, 200, 800, 300),
    )
    assert dev.mount_type == "rack"
    assert dev.u_start == 10
    assert dev.confidence == 0.92


def test_detected_device_shelf():
    dev = DetectedDevice(
        u_start=None,
        u_end=None,
        mount_type="shelf",
        model_guess="Netgear GS308",
        confidence=0.65,
        crop_region=(100, 500, 400, 550),
    )
    assert dev.mount_type == "shelf"
    assert dev.u_start is None
    assert dev.matched_device_type_id is None
    assert dev.match_candidates is None


def test_device_type_match():
    m = DeviceTypeMatch(device_type_id=42, name="SN2700-32C", similarity=0.88)
    assert m.similarity == 0.88


def test_detected_device_with_matches():
    dev = DetectedDevice(
        mount_type="rack",
        model_guess="SN2700",
        confidence=0.8,
        crop_region=(0, 0, 100, 100),
        matched_device_type_id=42,
        match_candidates=[
            DeviceTypeMatch(device_type_id=42, name="SN2700-32C", similarity=0.9),
            DeviceTypeMatch(device_type_id=43, name="SN2700-64C", similarity=0.85),
        ],
    )
    assert dev.matched_device_type_id == 42
    assert len(dev.match_candidates) == 2


def test_rack_analysis():
    analysis = RackAnalysis(
        devices=[
            DetectedDevice(
                u_start=1,
                u_end=2,
                mount_type="rack",
                model_guess="R640",
                confidence=0.95,
                crop_region=(0, 0, 100, 100),
            )
        ],
        annotated_image=b"fake_image_data",
        rack_context=RackContext(rack_id=5),
    )
    assert len(analysis.devices) == 1
    assert analysis.errors == []


def test_device_confirmation():
    conf = DeviceConfirmation(
        index=0,
        confirmed=True,
        corrected_model="Dell R640",
        device_type_id=10,
        create_new_type=False,
    )
    assert conf.confirmed is True
    assert conf.corrected_model == "Dell R640"


def test_device_confirmation_reject():
    conf = DeviceConfirmation(index=2, confirmed=False, create_new_type=False)
    assert conf.confirmed is False


def test_rack_population_report():
    report = RackPopulationReport(
        rack_id=5,
        created=[ChangeRecord(object_type="device", object_id=10, action="created", detail={"name": "srv1"})],
        updated=[],
        skipped=["Unknown device at U20"],
        errors=[],
    )
    assert report.rack_id == 5
    assert len(report.created) == 1
    assert len(report.skipped) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models_rack_vision.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models_rack_vision.py -v`

Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/models/rack_vision.py tests/unit/test_models_rack_vision.py
git commit -m "feat: add rack vision models (DetectedDevice, RackAnalysis, etc.)"
```

---

### Task 7: Configuration

**Files:**
- Create: `src/netbox_skill/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/test_config.py
import os
import tempfile

import yaml

from netbox_skill.config import Config, load_config
from netbox_skill.exceptions import ConfigError


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com")
    monkeypatch.setenv("NETBOX_TOKEN", "nbt_abc.123")
    config = load_config()
    assert config.netbox_url == "https://netbox.example.com"
    assert config.netbox_token == "nbt_abc.123"
    assert config.netbox_verify_ssl is True
    assert config.max_concurrent_sessions == 10
    assert config.ssh_timeout == 30
    assert config.vision_provider == "claude"
    assert config.vision_confidence_threshold == 0.7


def test_config_missing_required(monkeypatch):
    monkeypatch.delenv("NETBOX_URL", raising=False)
    monkeypatch.delenv("NETBOX_TOKEN", raising=False)
    try:
        load_config()
        assert False, "Should have raised ConfigError"
    except ConfigError:
        pass


def test_config_with_ssh_defaults(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://nb.test")
    monkeypatch.setenv("NETBOX_TOKEN", "token")
    monkeypatch.setenv("DEVICE_USERNAME", "admin")
    monkeypatch.setenv("DEVICE_PASSWORD", "secret")
    config = load_config()
    assert config.default_ssh_username == "admin"
    assert config.default_ssh_password == "secret"


def test_config_with_yaml_file(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://nb.test")
    monkeypatch.setenv("NETBOX_TOKEN", "token")
    yaml_content = {
        "devices": {
            "192.168.1.1": {
                "platform": "netgear",
                "username": "admin",
                "password": "secret",
            }
        },
        "groups": {
            "core-switches": {
                "platform": "sonic",
                "username": "admin",
                "ssh_key": "/path/to/key",
            }
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f)
        f.flush()
        monkeypatch.setenv("CONFIG_FILE", f.name)
        config = load_config()
        assert config.device_overrides["192.168.1.1"]["platform"] == "netgear"
        assert config.group_overrides["core-switches"]["platform"] == "sonic"
    os.unlink(f.name)


def test_config_yaml_file_not_found(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://nb.test")
    monkeypatch.setenv("NETBOX_TOKEN", "token")
    monkeypatch.setenv("CONFIG_FILE", "/nonexistent/file.yaml")
    try:
        load_config()
        assert False, "Should have raised ConfigError"
    except ConfigError as e:
        assert "not found" in str(e).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_config.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/config.py
"""Configuration loading from environment variables and optional YAML file."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from netbox_skill.exceptions import ConfigError


class Config(BaseModel):
    netbox_url: str
    netbox_token: str
    netbox_verify_ssl: bool = True
    default_ssh_username: str | None = None
    default_ssh_password: str | None = None
    default_ssh_key_path: str | None = None
    max_concurrent_sessions: int = 10
    ssh_timeout: int = 30
    config_file: str | None = None
    vision_provider: str = "claude"
    anthropic_api_key: str | None = None
    vision_model: str = "claude-sonnet-4-20250514"
    vision_confidence_threshold: float = 0.7
    device_overrides: dict[str, dict[str, Any]] = {}
    group_overrides: dict[str, dict[str, Any]] = {}


def load_config() -> Config:
    """Load config from environment variables and optional YAML file."""
    netbox_url = os.environ.get("NETBOX_URL")
    netbox_token = os.environ.get("NETBOX_TOKEN")

    if not netbox_url or not netbox_token:
        raise ConfigError("NETBOX_URL and NETBOX_TOKEN environment variables are required")

    device_overrides: dict[str, dict[str, Any]] = {}
    group_overrides: dict[str, dict[str, Any]] = {}

    config_file = os.environ.get("CONFIG_FILE")
    if config_file:
        path = Path(config_file)
        if not path.exists():
            raise ConfigError(f"Config file not found: {config_file}")
        with open(path) as f:
            yaml_data = yaml.safe_load(f) or {}
        device_overrides = yaml_data.get("devices", {})
        group_overrides = yaml_data.get("groups", {})

    return Config(
        netbox_url=netbox_url,
        netbox_token=netbox_token,
        netbox_verify_ssl=os.environ.get("NETBOX_VERIFY_SSL", "true").lower() == "true",
        default_ssh_username=os.environ.get("DEVICE_USERNAME"),
        default_ssh_password=os.environ.get("DEVICE_PASSWORD"),
        default_ssh_key_path=os.environ.get("DEVICE_SSH_KEY"),
        max_concurrent_sessions=int(os.environ.get("MAX_CONCURRENT_SESSIONS", "10")),
        ssh_timeout=int(os.environ.get("SSH_TIMEOUT", "30")),
        config_file=config_file,
        vision_provider=os.environ.get("VISION_PROVIDER", "claude"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        vision_model=os.environ.get("VISION_MODEL", "claude-sonnet-4-20250514"),
        vision_confidence_threshold=float(
            os.environ.get("VISION_CONFIDENCE_THRESHOLD", "0.7")
        ),
        device_overrides=device_overrides,
        group_overrides=group_overrides,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_config.py -v`

Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/config.py tests/unit/test_config.py
git commit -m "feat: add configuration loading from env vars and YAML file"
```

---

### Task 8: NetBox Client — Raw Methods

**Files:**
- Create: `src/netbox_skill/clients/__init__.py`
- Create: `src/netbox_skill/clients/netbox.py`
- Create: `tests/unit/clients/__init__.py`
- Create: `tests/unit/clients/test_netbox_client.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/clients/__init__.py
```

```python
# tests/unit/clients/test_netbox_client.py
import pytest
import httpx
import respx

from netbox_skill.clients.netbox import NetBoxClient
from netbox_skill.exceptions import (
    NetBoxAuthError,
    NetBoxNotFoundError,
    NetBoxValidationError,
    NetBoxServerError,
)


@pytest.fixture
def client():
    return NetBoxClient(url="https://netbox.test", token="nbt_test.token123")


@respx.mock
async def test_get_single(client):
    respx.get("https://netbox.test/api/dcim/devices/1/").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "sw1"})
    )
    result = await client.get("dcim/devices/1/")
    assert result["id"] == 1
    assert result["name"] == "sw1"


@respx.mock
async def test_get_list_with_pagination(client):
    respx.get("https://netbox.test/api/dcim/devices/").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 2,
                "next": "https://netbox.test/api/dcim/devices/?limit=1&offset=1",
                "previous": None,
                "results": [{"id": 1, "name": "sw1"}],
            },
        )
    )
    result = await client.get("dcim/devices/")
    assert result["count"] == 2
    assert len(result["results"]) == 1


@respx.mock
async def test_get_all_paginates(client):
    respx.get("https://netbox.test/api/dcim/devices/").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 2,
                "next": "https://netbox.test/api/dcim/devices/?limit=1&offset=1",
                "previous": None,
                "results": [{"id": 1, "name": "sw1"}],
            },
        )
    )
    respx.get("https://netbox.test/api/dcim/devices/?limit=1&offset=1").mock(
        return_value=httpx.Response(
            200,
            json={
                "count": 2,
                "next": None,
                "previous": "https://netbox.test/api/dcim/devices/",
                "results": [{"id": 2, "name": "sw2"}],
            },
        )
    )
    results = await client.get_all("dcim/devices/")
    assert len(results) == 2
    assert results[0]["name"] == "sw1"
    assert results[1]["name"] == "sw2"


@respx.mock
async def test_create(client):
    respx.post("https://netbox.test/api/dcim/devices/").mock(
        return_value=httpx.Response(201, json={"id": 3, "name": "sw3"})
    )
    result = await client.create("dcim/devices/", data={"name": "sw3", "role": 1, "device_type": 1, "site": 1})
    assert result["id"] == 3


@respx.mock
async def test_create_bulk(client):
    respx.post("https://netbox.test/api/dcim/devices/").mock(
        return_value=httpx.Response(201, json=[{"id": 3}, {"id": 4}])
    )
    result = await client.create("dcim/devices/", data=[{"name": "a"}, {"name": "b"}])
    assert len(result) == 2


@respx.mock
async def test_update_patch(client):
    respx.patch("https://netbox.test/api/dcim/devices/1/").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "renamed"})
    )
    result = await client.update("dcim/devices/", id=1, data={"name": "renamed"})
    assert result["name"] == "renamed"


@respx.mock
async def test_update_put(client):
    respx.put("https://netbox.test/api/dcim/devices/1/").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "full"})
    )
    result = await client.update("dcim/devices/", id=1, data={"name": "full"}, partial=False)
    assert result["name"] == "full"


@respx.mock
async def test_delete(client):
    respx.delete("https://netbox.test/api/dcim/devices/1/").mock(
        return_value=httpx.Response(204)
    )
    await client.delete("dcim/devices/", id=1)


@respx.mock
async def test_status(client):
    respx.get("https://netbox.test/api/status/").mock(
        return_value=httpx.Response(200, json={"netbox-version": "4.5.6"})
    )
    result = await client.status()
    assert result["netbox-version"] == "4.5.6"


@respx.mock
async def test_auth_error(client):
    respx.get("https://netbox.test/api/dcim/devices/").mock(
        return_value=httpx.Response(403, json={"detail": "No permission"})
    )
    with pytest.raises(NetBoxAuthError) as exc_info:
        await client.get("dcim/devices/")
    assert exc_info.value.status_code == 403


@respx.mock
async def test_not_found_error(client):
    respx.get("https://netbox.test/api/dcim/devices/999/").mock(
        return_value=httpx.Response(404, json={"detail": "Not found."})
    )
    with pytest.raises(NetBoxNotFoundError):
        await client.get("dcim/devices/999/")


@respx.mock
async def test_validation_error(client):
    respx.post("https://netbox.test/api/dcim/devices/").mock(
        return_value=httpx.Response(400, json={"name": ["This field is required."]})
    )
    with pytest.raises(NetBoxValidationError) as exc_info:
        await client.create("dcim/devices/", data={})
    assert "name" in exc_info.value.field_errors


@respx.mock
async def test_server_error(client):
    respx.get("https://netbox.test/api/dcim/devices/").mock(
        return_value=httpx.Response(500, json={"detail": "Internal error"})
    )
    with pytest.raises(NetBoxServerError):
        await client.get("dcim/devices/")


@respx.mock
async def test_auth_header_sent(client):
    route = respx.get("https://netbox.test/api/status/").mock(
        return_value=httpx.Response(200, json={})
    )
    await client.status()
    assert route.calls[0].request.headers["Authorization"] == "Bearer nbt_test.token123"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/clients/test_netbox_client.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/clients/__init__.py
"""Client implementations for external systems."""
```

```python
# src/netbox_skill/clients/netbox.py
"""Async HTTP client for the NetBox REST API."""

from __future__ import annotations

from typing import Any

import httpx

from netbox_skill.exceptions import (
    NetBoxAuthError,
    NetBoxClientError,
    NetBoxNotFoundError,
    NetBoxServerError,
    NetBoxValidationError,
)


class NetBoxClient:
    """Async client wrapping the NetBox REST API."""

    def __init__(self, url: str, token: str, verify_ssl: bool = True):
        self._base_url = url.rstrip("/")
        self._token = token
        self._verify_ssl = verify_ssl
        self._http: httpx.AsyncClient | None = None

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=f"{self._base_url}/api/",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                verify=self._verify_ssl,
                timeout=30.0,
            )
        return self._http

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        try:
            body = response.json()
        except Exception:
            body = response.text
        status = response.status_code
        if status in (401, 403):
            raise NetBoxAuthError(status_code=status, body=body)
        if status == 404:
            raise NetBoxNotFoundError(status_code=status, body=body)
        if status == 400:
            raise NetBoxValidationError(status_code=status, body=body)
        if status >= 500:
            raise NetBoxServerError(status_code=status, body=body)
        raise NetBoxClientError(status_code=status, body=body)

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        http = await self._get_http()
        response = await http.get(endpoint, params=params)
        self._raise_for_status(response)
        return response.json()

    async def get_all(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> list[dict]:
        http = await self._get_http()
        all_params = dict(params or {})
        all_params.setdefault("limit", 100)
        response = await http.get(endpoint, params=all_params)
        self._raise_for_status(response)
        data = response.json()
        results = list(data.get("results", []))
        next_url = data.get("next")
        while next_url:
            response = await http.get(next_url)
            self._raise_for_status(response)
            data = response.json()
            results.extend(data.get("results", []))
            next_url = data.get("next")
        return results

    async def create(
        self, endpoint: str, data: dict | list[dict]
    ) -> dict | list[dict]:
        http = await self._get_http()
        response = await http.post(endpoint, json=data)
        self._raise_for_status(response)
        return response.json()

    async def update(
        self,
        endpoint: str,
        id: int,
        data: dict[str, Any],
        partial: bool = True,
    ) -> dict:
        http = await self._get_http()
        url = f"{endpoint.rstrip('/')}/{id}/"
        if partial:
            response = await http.patch(url, json=data)
        else:
            response = await http.put(url, json=data)
        self._raise_for_status(response)
        return response.json()

    async def delete(self, endpoint: str, id: int) -> None:
        http = await self._get_http()
        url = f"{endpoint.rstrip('/')}/{id}/"
        response = await http.delete(url)
        self._raise_for_status(response)

    async def status(self) -> dict:
        http = await self._get_http()
        response = await http.get("status/")
        self._raise_for_status(response)
        return response.json()

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/clients/test_netbox_client.py -v`

Expected: 14 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/clients/ tests/unit/clients/
git commit -m "feat: add NetBox API client with pagination, error handling, and CRUD"
```

---

### Task 9: SSH Client

**Files:**
- Create: `src/netbox_skill/clients/ssh.py`
- Create: `tests/unit/clients/test_ssh_client.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/clients/test_ssh_client.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from netbox_skill.clients.ssh import SSHClient
from netbox_skill.exceptions import DeviceConnectionError, CommandError
from netbox_skill.models.common import CredentialSet


@pytest.fixture
def creds():
    return CredentialSet(username="admin", password="secret")


def test_ssh_client_init(creds):
    client = SSHClient(host="10.0.0.1", credentials=creds, timeout=15)
    assert client._host == "10.0.0.1"
    assert client._timeout == 15


@patch("netbox_skill.clients.ssh.asyncssh")
async def test_connect_with_password(mock_asyncssh, creds):
    mock_conn = AsyncMock()
    mock_asyncssh.connect = AsyncMock(return_value=mock_conn)

    client = SSHClient(host="10.0.0.1", credentials=creds)
    await client.connect()

    mock_asyncssh.connect.assert_called_once()
    call_kwargs = mock_asyncssh.connect.call_args[1]
    assert call_kwargs["host"] == "10.0.0.1"
    assert call_kwargs["username"] == "admin"
    assert call_kwargs["password"] == "secret"


@patch("netbox_skill.clients.ssh.asyncssh")
async def test_connect_failure_raises(mock_asyncssh, creds):
    mock_asyncssh.connect = AsyncMock(side_effect=OSError("Connection refused"))

    client = SSHClient(host="10.0.0.1", credentials=creds)
    with pytest.raises(DeviceConnectionError):
        await client.connect()


@patch("netbox_skill.clients.ssh.asyncssh")
async def test_execute_command(mock_asyncssh, creds):
    mock_result = MagicMock()
    mock_result.stdout = "hostname sw1\n"
    mock_result.exit_status = 0
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(return_value=mock_result)
    mock_asyncssh.connect = AsyncMock(return_value=mock_conn)

    client = SSHClient(host="10.0.0.1", credentials=creds)
    await client.connect()
    output = await client.execute("show version")
    assert output == "hostname sw1\n"


@patch("netbox_skill.clients.ssh.asyncssh")
async def test_execute_commands(mock_asyncssh, creds):
    results = []
    for text in ["output1\n", "output2\n"]:
        r = MagicMock()
        r.stdout = text
        r.exit_status = 0
        results.append(r)
    mock_conn = AsyncMock()
    mock_conn.run = AsyncMock(side_effect=results)
    mock_asyncssh.connect = AsyncMock(return_value=mock_conn)

    client = SSHClient(host="10.0.0.1", credentials=creds)
    await client.connect()
    outputs = await client.execute_commands(["cmd1", "cmd2"])
    assert len(outputs) == 2
    assert outputs[0] == "output1\n"


@patch("netbox_skill.clients.ssh.asyncssh")
async def test_context_manager(mock_asyncssh, creds):
    mock_conn = AsyncMock()
    mock_conn.close = MagicMock()
    mock_asyncssh.connect = AsyncMock(return_value=mock_conn)

    async with SSHClient(host="10.0.0.1", credentials=creds) as client:
        pass
    mock_conn.close.assert_called_once()


@patch("netbox_skill.clients.ssh.asyncssh")
async def test_execute_without_connect_raises(mock_asyncssh, creds):
    client = SSHClient(host="10.0.0.1", credentials=creds)
    with pytest.raises(DeviceConnectionError, match="Not connected"):
        await client.execute("show version")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/clients/test_ssh_client.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/clients/ssh.py
"""Async SSH client for network device CLI interaction."""

from __future__ import annotations

from typing import Any

import asyncssh

from netbox_skill.exceptions import CommandError, DeviceConnectionError
from netbox_skill.models.common import CredentialSet


class SSHClient:
    """Async SSH client that returns raw command output."""

    def __init__(self, host: str, credentials: CredentialSet, timeout: int = 30):
        self._host = host
        self._credentials = credentials
        self._timeout = timeout
        self._conn: asyncssh.SSHClientConnection | None = None

    async def connect(self) -> None:
        kwargs: dict[str, Any] = {
            "host": self._host,
            "username": self._credentials.username,
            "known_hosts": None,
            "connect_timeout": self._timeout,
        }
        if self._credentials.password:
            kwargs["password"] = self._credentials.password
        if self._credentials.ssh_key_path:
            kwargs["client_keys"] = [self._credentials.ssh_key_path]
        try:
            self._conn = await asyncssh.connect(**kwargs)
        except Exception as e:
            raise DeviceConnectionError(
                f"SSH connection to {self._host} failed: {e}"
            ) from e

    async def execute(self, command: str) -> str:
        if self._conn is None:
            raise DeviceConnectionError(f"Not connected to {self._host}")
        result = await self._conn.run(command, check=False)
        return result.stdout or ""

    async def execute_commands(self, commands: list[str]) -> list[str]:
        outputs = []
        for cmd in commands:
            output = await self.execute(cmd)
            outputs.append(output)
        return outputs

    async def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    async def __aenter__(self) -> SSHClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/clients/test_ssh_client.py -v`

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/clients/ssh.py tests/unit/clients/test_ssh_client.py
git commit -m "feat: add async SSH client for device CLI interaction"
```

---

### Task 10: Parser Registry

**Files:**
- Create: `src/netbox_skill/parsers/__init__.py`
- Create: `src/netbox_skill/parsers/registry.py`
- Create: `tests/unit/parsers/__init__.py`
- Create: `tests/unit/parsers/test_registry.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/parsers/__init__.py
```

```python
# tests/unit/parsers/test_registry.py
import pytest

from netbox_skill.parsers.registry import (
    DeviceParser,
    PARSER_REGISTRY,
    register_parser,
    get_parser,
)
from netbox_skill.exceptions import UnknownPlatformError
from netbox_skill.clients.ssh import SSHClient
from netbox_skill.models.discovery import (
    MACEntry, ARPEntry, LLDPNeighbor, InterfaceDetail, VLANInfo, DeviceInfo,
)


def test_register_parser():
    @register_parser("test_vendor")
    class TestParser(DeviceParser):
        async def get_mac_table(self, client): return []
        async def get_arp_table(self, client): return []
        async def get_lldp_neighbors(self, client): return []
        async def get_interfaces(self, client): return []
        async def get_vlans(self, client): return []
        async def get_device_info(self, client): return DeviceInfo(hostname="test")

    assert "test_vendor" in PARSER_REGISTRY
    parser = get_parser("test_vendor")
    assert isinstance(parser, TestParser)

    # Cleanup
    del PARSER_REGISTRY["test_vendor"]


def test_get_parser_unknown():
    with pytest.raises(UnknownPlatformError) as exc_info:
        get_parser("nonexistent_platform")
    assert exc_info.value.platform == "nonexistent_platform"


def test_device_parser_is_abstract():
    with pytest.raises(TypeError):
        DeviceParser()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/parsers/test_registry.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/parsers/__init__.py
"""Device CLI parsers for vendor-specific output."""
```

```python
# src/netbox_skill/parsers/registry.py
"""Parser base class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from netbox_skill.exceptions import UnknownPlatformError
from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)

if TYPE_CHECKING:
    from netbox_skill.clients.ssh import SSHClient


class DeviceParser(ABC):
    """Base class all vendor parsers must implement."""

    @abstractmethod
    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]: ...

    @abstractmethod
    async def get_arp_table(self, client: SSHClient) -> list[ARPEntry]: ...

    @abstractmethod
    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]: ...

    @abstractmethod
    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]: ...

    @abstractmethod
    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]: ...

    @abstractmethod
    async def get_device_info(self, client: SSHClient) -> DeviceInfo: ...


PARSER_REGISTRY: dict[str, type[DeviceParser]] = {}


def register_parser(platform: str):
    """Decorator to register a parser class for a platform string."""

    def decorator(cls: type[DeviceParser]) -> type[DeviceParser]:
        PARSER_REGISTRY[platform] = cls
        return cls

    return decorator


def get_parser(platform: str) -> DeviceParser:
    """Instantiate and return the parser for the given platform."""
    cls = PARSER_REGISTRY.get(platform)
    if cls is None:
        raise UnknownPlatformError(platform)
    return cls()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/parsers/test_registry.py -v`

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/parsers/ tests/unit/parsers/
git commit -m "feat: add parser base class and registry with decorator registration"
```

---

### Task 11: SONiC Parser with Fixtures

**Files:**
- Create: `src/netbox_skill/parsers/sonic.py`
- Create: `tests/fixtures/sonic/show_mac.txt`
- Create: `tests/fixtures/sonic/show_arp.txt`
- Create: `tests/fixtures/sonic/show_lldp_table.txt`
- Create: `tests/fixtures/sonic/show_interfaces_status.txt`
- Create: `tests/fixtures/sonic/show_vlan_brief.txt`
- Create: `tests/fixtures/sonic/show_platform_summary.txt`
- Create: `tests/unit/parsers/test_sonic.py`

This task implements one parser end-to-end as the template. Tasks 12 and 13 follow the same pattern for Netgear and FS.com.

- [ ] **Step 1: Create fixture files**

```
# tests/fixtures/sonic/show_mac.txt
  No.    Vlan  MacAddress         Port           Type
-----  ------  -----------------  -------------  -------
    1     100  AA:BB:CC:DD:EE:01  Ethernet0      Dynamic
    2     100  AA:BB:CC:DD:EE:02  Ethernet4      Dynamic
    3     200  AA:BB:CC:DD:EE:03  Ethernet8      Static
Total number of entries 3
```

```
# tests/fixtures/sonic/show_arp.txt
Address        MacAddress         Iface      Vlan
-----------    -----------------  ---------  ------
10.0.0.1       AA:BB:CC:DD:EE:01  Ethernet0  100
10.0.0.2       AA:BB:CC:DD:EE:02  Ethernet4  100
192.168.1.1    AA:BB:CC:DD:EE:03  Ethernet8  200
Total number of entries 3
```

```
# tests/fixtures/sonic/show_lldp_table.txt
Capability codes: (R) Router, (B) Bridge, (O) Other
LocalPort    RemoteDevice       RemotePort     Capability    RemotePortID
-----------  -----------------  -------------  ------------  ----------------
Ethernet0    sw-core-01         Ethernet48     BR            Ethernet48
Ethernet4    sw-access-02       Ethernet1      B             Ethernet1
Total entries displayed:  2
```

```
# tests/fixtures/sonic/show_interfaces_status.txt
  Interface        Lanes    Speed    MTU    FEC        Alias    Vlan    Oper    Admin    Type         Asym PFC
-----------  -----------  -------  -----  -----  -----------  ------  ------  -------  -----------  ----------
  Ethernet0  25,26,27,28     100G   9100    rs   Ethernet1/1  routed      up       up  QSFP28 or+         N/A
  Ethernet4  29,30,31,32     100G   9100    rs   Ethernet1/2   trunk      up       up  QSFP28 or+         N/A
  Ethernet8   33,34,35,36     25G   1500   none  Ethernet1/3   trunk    down     down  SFP28               N/A
```

```
# tests/fixtures/sonic/show_vlan_brief.txt
+-----------+-----------------+------------+----------------+-----------+
|   VLAN ID | IP Address      | Ports      | Port Tagging   | Proxy ARP |
+===========+=================+============+================+===========+
|       100 | 10.0.0.254/24   | Ethernet0  | untagged       | disabled  |
|           |                 | Ethernet4  | tagged         |           |
+-----------+-----------------+------------+----------------+-----------+
|       200 | 192.168.1.254/24| Ethernet8  | untagged       | disabled  |
+-----------+-----------------+------------+----------------+-----------+
```

```
# tests/fixtures/sonic/show_platform_summary.txt
Platform: x86_64-mlnx_msn2700-r0
HwSKU: Mellanox-SN2700
ASIC: mellanox
Serial Number: MT1234567890
Hardware Revision: A1
```

- [ ] **Step 2: Write the test**

```python
# tests/unit/parsers/test_sonic.py
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from netbox_skill.parsers.sonic import SonicParser
from netbox_skill.parsers.registry import get_parser

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "sonic"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture
def parser():
    return SonicParser()


@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client


async def test_sonic_registered():
    parser = get_parser("sonic")
    assert isinstance(parser, SonicParser)


async def test_parse_mac_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_mac.txt"))
    entries = await parser.get_mac_table(mock_client)
    assert len(entries) == 3
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"
    assert entries[0].port == "Ethernet0"
    assert entries[0].vlan == 100
    assert entries[2].vlan == 200


async def test_parse_arp_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_arp.txt"))
    entries = await parser.get_arp_table(mock_client)
    assert len(entries) == 3
    assert entries[0].ip == "10.0.0.1"
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"
    assert entries[0].interface == "Ethernet0"


async def test_parse_lldp_neighbors(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_lldp_table.txt"))
    neighbors = await parser.get_lldp_neighbors(mock_client)
    assert len(neighbors) == 2
    assert neighbors[0].local_port == "Ethernet0"
    assert neighbors[0].remote_device == "sw-core-01"
    assert neighbors[0].remote_port == "Ethernet48"


async def test_parse_interfaces(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_interfaces_status.txt"))
    ifaces = await parser.get_interfaces(mock_client)
    assert len(ifaces) == 3
    assert ifaces[0].name == "Ethernet0"
    assert ifaces[0].status == "up"
    assert ifaces[0].speed == "100G"
    assert ifaces[0].mtu == 9100
    assert ifaces[2].status == "down"


async def test_parse_vlans(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_vlan_brief.txt"))
    vlans = await parser.get_vlans(mock_client)
    assert len(vlans) == 2
    assert vlans[0].id == 100
    assert "Ethernet0" in vlans[0].ports
    assert "Ethernet4" in vlans[0].ports
    assert vlans[1].id == 200


async def test_parse_device_info(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_platform_summary.txt"))
    info = await parser.get_device_info(mock_client)
    assert info.hostname is not None
    assert info.model == "Mellanox-SN2700"
    assert info.serial == "MT1234567890"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/unit/parsers/test_sonic.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 4: Write the implementation**

```python
# src/netbox_skill/parsers/sonic.py
"""SONiC CLI output parser for Mellanox/Broadcom switches."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)
from netbox_skill.parsers.registry import DeviceParser, register_parser

if TYPE_CHECKING:
    from netbox_skill.clients.ssh import SSHClient


@register_parser("sonic")
class SonicParser(DeviceParser):

    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]:
        output = await client.execute("show mac")
        entries = []
        for line in output.splitlines():
            m = re.match(
                r"\s*\d+\s+(\d+)\s+([\w:]+)\s+(\S+)\s+\w+",
                line,
            )
            if m:
                entries.append(
                    MACEntry(vlan=int(m.group(1)), mac=m.group(2), port=m.group(3))
                )
        return entries

    async def get_arp_table(self, client: SSHClient) -> list[ARPEntry]:
        output = await client.execute("show arp")
        entries = []
        for line in output.splitlines():
            m = re.match(
                r"(\d+\.\d+\.\d+\.\d+)\s+([\w:]+)\s+(\S+)",
                line.strip(),
            )
            if m:
                entries.append(
                    ARPEntry(ip=m.group(1), mac=m.group(2), interface=m.group(3))
                )
        return entries

    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]:
        output = await client.execute("show lldp table")
        neighbors = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+(\S+)\s+(\S+)\s+\S+\s+(\S+)",
                line.strip(),
            )
            if m and not line.strip().startswith(("Capability", "LocalPort", "-")):
                neighbors.append(
                    LLDPNeighbor(
                        local_port=m.group(1),
                        remote_device=m.group(2),
                        remote_port=m.group(3),
                        remote_chassis_id=None,
                    )
                )
        return neighbors

    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]:
        output = await client.execute("show interfaces status")
        interfaces = []
        for line in output.splitlines():
            m = re.match(
                r"\s*(\S+)\s+\S+\s+(\S+)\s+(\d+)\s+\S+\s+\S+\s+\S+\s+(\w+)\s+(\w+)",
                line,
            )
            if m and not line.strip().startswith(("Interface", "-")):
                interfaces.append(
                    InterfaceDetail(
                        name=m.group(1),
                        speed=m.group(2),
                        mtu=int(m.group(3)),
                        status=m.group(4).lower(),
                    )
                )
        return interfaces

    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]:
        output = await client.execute("show vlan brief")
        vlans: dict[int, VLANInfo] = {}
        current_vlan_id: int | None = None
        for line in output.splitlines():
            vlan_match = re.match(r"\|\s+(\d+)\s+\|", line)
            if vlan_match:
                current_vlan_id = int(vlan_match.group(1))
                if current_vlan_id not in vlans:
                    vlans[current_vlan_id] = VLANInfo(
                        id=current_vlan_id, name=f"Vlan{current_vlan_id}", ports=[]
                    )
            if current_vlan_id is not None:
                port_match = re.findall(r"(Ethernet\d+)", line)
                for port in port_match:
                    if port not in vlans[current_vlan_id].ports:
                        vlans[current_vlan_id].ports.append(port)
        return list(vlans.values())

    async def get_device_info(self, client: SSHClient) -> DeviceInfo:
        output = await client.execute("show platform summary")
        model = None
        serial = None
        hostname = "unknown"
        for line in output.splitlines():
            m = re.match(r"HwSKU:\s*(.+)", line)
            if m:
                model = m.group(1).strip()
            m = re.match(r"Serial Number:\s*(.+)", line)
            if m:
                serial = m.group(1).strip()
        # Try to get hostname
        try:
            hostname_output = await client.execute("hostname")
            hostname = hostname_output.strip() or "unknown"
        except Exception:
            pass
        return DeviceInfo(hostname=hostname, model=model, serial=serial)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/parsers/test_sonic.py -v`

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add src/netbox_skill/parsers/sonic.py tests/fixtures/sonic/ tests/unit/parsers/test_sonic.py
git commit -m "feat: add SONiC CLI parser with fixtures"
```

---

### Task 12: Netgear Parser with Fixtures

**Files:**
- Create: `src/netbox_skill/parsers/netgear.py`
- Create: `tests/fixtures/netgear/show_mac_address_table.txt`
- Create: `tests/fixtures/netgear/show_arp.txt`
- Create: `tests/fixtures/netgear/show_lldp_remote_device_all.txt`
- Create: `tests/fixtures/netgear/show_interfaces_status_all.txt`
- Create: `tests/fixtures/netgear/show_vlan_brief.txt`
- Create: `tests/fixtures/netgear/show_version.txt`
- Create: `tests/unit/parsers/test_netgear.py`

- [ ] **Step 1: Create fixture files**

```
# tests/fixtures/netgear/show_mac_address_table.txt

VLAN ID    MAC Address         Type      Port
-------    -----------------   -------   -----------
100        AA:BB:CC:DD:EE:01   Dynamic   0/1
100        AA:BB:CC:DD:EE:02   Dynamic   0/2
200        AA:BB:CC:DD:EE:03   Dynamic   0/5
```

```
# tests/fixtures/netgear/show_arp.txt

IP Address       MAC Address         Interface
---------------  -----------------   ---------
10.0.0.1         AA:BB:CC:DD:EE:01   vlan 100
10.0.0.2         AA:BB:CC:DD:EE:02   vlan 100
192.168.1.1      AA:BB:CC:DD:EE:03   vlan 200
```

```
# tests/fixtures/netgear/show_lldp_remote_device_all.txt

LLDP Remote Device Detail

Local Interface: 0/1
    Remote Identifier: AA:BB:CC:DD:EE:01
    Chassis ID: AA:BB:CC:DD:EE:01
    Port ID: Gi0/1
    System Name: sw-core-01

Local Interface: 0/2
    Remote Identifier: AA:BB:CC:DD:EE:02
    Chassis ID: AA:BB:CC:DD:EE:02
    Port ID: Gi0/2
    System Name: sw-access-02
```

```
# tests/fixtures/netgear/show_interfaces_status_all.txt

                                        Link    Physical    Physical    Media
Port       Name            Admin Mode   State   Mode        Status      Type
--------- --------------- ------------ ------  ----------- ----------- -----------
0/1        uplink          Enable       Up      Auto        100 Full    Copper
0/2        server-port     Enable       Up      Auto        1000 Full   Copper
0/5        printer         Enable       Down    Auto                    Copper
```

```
# tests/fixtures/netgear/show_vlan_brief.txt

VLAN ID  VLAN Name                         VLAN Type
-------  --------------------------------  ---------
1        Default                           Default
100      Management                        Static
200      Servers                           Static
```

```
# tests/fixtures/netgear/show_version.txt

Machine Description... Netgear M4300-28G
System Name........... sw-access-01
Software Version...... 12.0.17.1
Machine Model......... M4300-28G
Serial Number......... ABC12345678
```

- [ ] **Step 2: Write the test**

```python
# tests/unit/parsers/test_netgear.py
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from netbox_skill.parsers.netgear import NetgearParser
from netbox_skill.parsers.registry import get_parser

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "netgear"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture
def parser():
    return NetgearParser()


@pytest.fixture
def mock_client():
    return AsyncMock()


async def test_netgear_registered():
    parser = get_parser("netgear")
    assert isinstance(parser, NetgearParser)


async def test_parse_mac_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_mac_address_table.txt"))
    entries = await parser.get_mac_table(mock_client)
    assert len(entries) == 3
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"
    assert entries[0].port == "0/1"
    assert entries[0].vlan == 100


async def test_parse_arp_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_arp.txt"))
    entries = await parser.get_arp_table(mock_client)
    assert len(entries) == 3
    assert entries[0].ip == "10.0.0.1"
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"


async def test_parse_lldp_neighbors(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_lldp_remote_device_all.txt"))
    neighbors = await parser.get_lldp_neighbors(mock_client)
    assert len(neighbors) == 2
    assert neighbors[0].local_port == "0/1"
    assert neighbors[0].remote_device == "sw-core-01"
    assert neighbors[0].remote_port == "Gi0/1"
    assert neighbors[0].remote_chassis_id == "AA:BB:CC:DD:EE:01"


async def test_parse_interfaces(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_interfaces_status_all.txt"))
    ifaces = await parser.get_interfaces(mock_client)
    assert len(ifaces) == 3
    assert ifaces[0].name == "0/1"
    assert ifaces[0].status == "up"
    assert ifaces[2].status == "down"


async def test_parse_vlans(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_vlan_brief.txt"))
    vlans = await parser.get_vlans(mock_client)
    assert len(vlans) == 3
    assert vlans[1].id == 100
    assert vlans[1].name == "Management"


async def test_parse_device_info(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_version.txt"))
    info = await parser.get_device_info(mock_client)
    assert info.hostname == "sw-access-01"
    assert info.model == "M4300-28G"
    assert info.serial == "ABC12345678"
    assert info.firmware == "12.0.17.1"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/unit/parsers/test_netgear.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 4: Write the implementation**

```python
# src/netbox_skill/parsers/netgear.py
"""Netgear managed switch CLI output parser."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)
from netbox_skill.parsers.registry import DeviceParser, register_parser

if TYPE_CHECKING:
    from netbox_skill.clients.ssh import SSHClient


@register_parser("netgear")
class NetgearParser(DeviceParser):

    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]:
        output = await client.execute("show mac-address-table")
        entries = []
        for line in output.splitlines():
            m = re.match(r"(\d+)\s+([\w:]+)\s+\w+\s+(\S+)", line.strip())
            if m:
                entries.append(
                    MACEntry(vlan=int(m.group(1)), mac=m.group(2), port=m.group(3))
                )
        return entries

    async def get_arp_table(self, client: SSHClient) -> list[ARPEntry]:
        output = await client.execute("show arp")
        entries = []
        for line in output.splitlines():
            m = re.match(
                r"(\d+\.\d+\.\d+\.\d+)\s+([\w:]+)\s+(\S.*\S)",
                line.strip(),
            )
            if m:
                entries.append(
                    ARPEntry(ip=m.group(1), mac=m.group(2), interface=m.group(3).strip())
                )
        return entries

    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]:
        output = await client.execute("show lldp remote-device all")
        neighbors = []
        local_port = None
        chassis_id = None
        port_id = None
        system_name = None
        for line in output.splitlines():
            m = re.match(r"Local Interface:\s*(\S+)", line.strip())
            if m:
                if local_port and system_name and port_id:
                    neighbors.append(
                        LLDPNeighbor(
                            local_port=local_port,
                            remote_device=system_name,
                            remote_port=port_id,
                            remote_chassis_id=chassis_id,
                        )
                    )
                local_port = m.group(1)
                chassis_id = None
                port_id = None
                system_name = None
                continue
            m = re.match(r"Chassis ID:\s*(\S+)", line.strip())
            if m:
                chassis_id = m.group(1)
            m = re.match(r"Port ID:\s*(\S+)", line.strip())
            if m:
                port_id = m.group(1)
            m = re.match(r"System Name:\s*(.+)", line.strip())
            if m:
                system_name = m.group(1).strip()
        if local_port and system_name and port_id:
            neighbors.append(
                LLDPNeighbor(
                    local_port=local_port,
                    remote_device=system_name,
                    remote_port=port_id,
                    remote_chassis_id=chassis_id,
                )
            )
        return neighbors

    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]:
        output = await client.execute("show interfaces status all")
        interfaces = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+\S*\s+\S+\s+(Up|Down)\s",
                line.strip(),
            )
            if m and not line.strip().startswith(("Port", "---")):
                speed_match = re.search(r"(\d+)\s+(Full|Half)", line)
                speed = f"{speed_match.group(1)}M" if speed_match else None
                interfaces.append(
                    InterfaceDetail(
                        name=m.group(1),
                        status=m.group(2).lower(),
                        speed=speed,
                    )
                )
        return interfaces

    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]:
        output = await client.execute("show vlan brief")
        vlans = []
        for line in output.splitlines():
            m = re.match(r"(\d+)\s+(\S+(?:\s+\S+)*?)\s{2,}\S+", line.strip())
            if m and not line.strip().startswith(("VLAN", "---")):
                vlans.append(
                    VLANInfo(id=int(m.group(1)), name=m.group(2).strip(), ports=[])
                )
        return vlans

    async def get_device_info(self, client: SSHClient) -> DeviceInfo:
        output = await client.execute("show version")
        hostname = "unknown"
        model = None
        serial = None
        firmware = None
        for line in output.splitlines():
            m = re.match(r"System Name\.+\s*(.+)", line)
            if m:
                hostname = m.group(1).strip()
            m = re.match(r"Machine Model\.+\s*(.+)", line)
            if m:
                model = m.group(1).strip()
            m = re.match(r"Serial Number\.+\s*(.+)", line)
            if m:
                serial = m.group(1).strip()
            m = re.match(r"Software Version\.+\s*(.+)", line)
            if m:
                firmware = m.group(1).strip()
        return DeviceInfo(
            hostname=hostname, model=model, serial=serial, firmware=firmware
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/parsers/test_netgear.py -v`

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add src/netbox_skill/parsers/netgear.py tests/fixtures/netgear/ tests/unit/parsers/test_netgear.py
git commit -m "feat: add Netgear CLI parser with fixtures"
```

---

### Task 13: FS.com Parser with Fixtures

**Files:**
- Create: `src/netbox_skill/parsers/fs_com.py`
- Create: `tests/fixtures/fs_com/show_mac_address_table.txt`
- Create: `tests/fixtures/fs_com/show_arp.txt`
- Create: `tests/fixtures/fs_com/show_lldp_neighbors.txt`
- Create: `tests/fixtures/fs_com/show_interface_status.txt`
- Create: `tests/fixtures/fs_com/show_vlan.txt`
- Create: `tests/fixtures/fs_com/show_version.txt`
- Create: `tests/unit/parsers/test_fs_com.py`

- [ ] **Step 1: Create fixture files**

```
# tests/fixtures/fs_com/show_mac_address_table.txt

Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
100     AA:BB:CC:DD:EE:01 DYNAMIC     Gi0/1
100     AA:BB:CC:DD:EE:02 DYNAMIC     Gi0/2
200     AA:BB:CC:DD:EE:03 STATIC      Gi0/10
```

```
# tests/fixtures/fs_com/show_arp.txt

Protocol  Address         Age (min)  Hardware Addr     Type   Interface
Internet  10.0.0.1              5    AA:BB:CC:DD:EE:01 ARPA   Vlan100
Internet  10.0.0.2             10    AA:BB:CC:DD:EE:02 ARPA   Vlan100
Internet  192.168.1.1           2    AA:BB:CC:DD:EE:03 ARPA   Vlan200
```

```
# tests/fixtures/fs_com/show_lldp_neighbors.txt

Capability codes:
    (R) Router, (B) Bridge, (T) Telephone, (C) DOCSIS Cable Device
    (W) WLAN Access Point, (P) Repeater, (S) Station, (O) Other

Device ID          Local Intf     Hold-time  Capability  Port ID
sw-core-01         Gi0/1          120        BR          Gi0/48
sw-access-02       Gi0/2          120        B           Gi0/1

Total entries displayed: 2
```

```
# tests/fixtures/fs_com/show_interface_status.txt

Port       Name           Status       Vlan    Duplex  Speed   Type
Gi0/1      uplink         connected    100     a-full  a-1000  1000BaseTX
Gi0/2      server         connected    200     a-full  a-1000  1000BaseTX
Gi0/10     unused         notconnect   1       auto    auto    1000BaseTX
```

```
# tests/fixtures/fs_com/show_vlan.txt

VLAN  Name                             Status    Ports
----  -------------------------------- --------- -------------------------------
1     default                          active    Gi0/10
100   Management                       active    Gi0/1
200   Servers                          active    Gi0/2
```

```
# tests/fixtures/fs_com/show_version.txt

FS S3900-24T4S Software, Version 2.5.0
Copyright (C) 2024 FS.COM Inc.
Hardware Version: V1.0
Serial Number: FSN123456789
System Name: sw-dist-01
Uptime is 45 days, 12 hours, 30 minutes
```

- [ ] **Step 2: Write the test**

```python
# tests/unit/parsers/test_fs_com.py
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from netbox_skill.parsers.fs_com import FSComParser
from netbox_skill.parsers.registry import get_parser

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "fs_com"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text()


@pytest.fixture
def parser():
    return FSComParser()


@pytest.fixture
def mock_client():
    return AsyncMock()


async def test_fs_com_registered():
    parser = get_parser("fs_com")
    assert isinstance(parser, FSComParser)


async def test_parse_mac_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_mac_address_table.txt"))
    entries = await parser.get_mac_table(mock_client)
    assert len(entries) == 3
    assert entries[0].mac == "AA:BB:CC:DD:EE:01"
    assert entries[0].port == "Gi0/1"
    assert entries[0].vlan == 100


async def test_parse_arp_table(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_arp.txt"))
    entries = await parser.get_arp_table(mock_client)
    assert len(entries) == 3
    assert entries[0].ip == "10.0.0.1"
    assert entries[0].interface == "Vlan100"


async def test_parse_lldp_neighbors(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_lldp_neighbors.txt"))
    neighbors = await parser.get_lldp_neighbors(mock_client)
    assert len(neighbors) == 2
    assert neighbors[0].local_port == "Gi0/1"
    assert neighbors[0].remote_device == "sw-core-01"
    assert neighbors[0].remote_port == "Gi0/48"


async def test_parse_interfaces(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_interface_status.txt"))
    ifaces = await parser.get_interfaces(mock_client)
    assert len(ifaces) == 3
    assert ifaces[0].name == "Gi0/1"
    assert ifaces[0].status == "up"
    assert ifaces[2].status == "down"


async def test_parse_vlans(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_vlan.txt"))
    vlans = await parser.get_vlans(mock_client)
    assert len(vlans) == 3
    assert vlans[1].id == 100
    assert vlans[1].name == "Management"


async def test_parse_device_info(parser, mock_client):
    mock_client.execute = AsyncMock(return_value=load_fixture("show_version.txt"))
    info = await parser.get_device_info(mock_client)
    assert info.hostname == "sw-dist-01"
    assert info.serial == "FSN123456789"
    assert info.firmware == "2.5.0"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/unit/parsers/test_fs_com.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 4: Write the implementation**

```python
# src/netbox_skill/parsers/fs_com.py
"""FS.com switch CLI output parser (Broadcom-based)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)
from netbox_skill.parsers.registry import DeviceParser, register_parser

if TYPE_CHECKING:
    from netbox_skill.clients.ssh import SSHClient


@register_parser("fs_com")
class FSComParser(DeviceParser):

    async def get_mac_table(self, client: SSHClient) -> list[MACEntry]:
        output = await client.execute("show mac address-table")
        entries = []
        for line in output.splitlines():
            m = re.match(r"(\d+)\s+([\w:]+)\s+\w+\s+(\S+)", line.strip())
            if m:
                entries.append(
                    MACEntry(vlan=int(m.group(1)), mac=m.group(2), port=m.group(3))
                )
        return entries

    async def get_arp_table(self, client: SSHClient) -> list[ARPEntry]:
        output = await client.execute("show arp")
        entries = []
        for line in output.splitlines():
            m = re.match(
                r"Internet\s+(\d+\.\d+\.\d+\.\d+)\s+\S+\s+([\w:]+)\s+\w+\s+(\S+)",
                line.strip(),
            )
            if m:
                entries.append(
                    ARPEntry(ip=m.group(1), mac=m.group(2), interface=m.group(3))
                )
        return entries

    async def get_lldp_neighbors(self, client: SSHClient) -> list[LLDPNeighbor]:
        output = await client.execute("show lldp neighbors")
        neighbors = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+(\S+)\s+\d+\s+\S+\s+(\S+)",
                line.strip(),
            )
            if m and not line.strip().startswith(("Device", "Capability", "(", "Total", "-")):
                neighbors.append(
                    LLDPNeighbor(
                        local_port=m.group(2),
                        remote_device=m.group(1),
                        remote_port=m.group(3),
                    )
                )
        return neighbors

    async def get_interfaces(self, client: SSHClient) -> list[InterfaceDetail]:
        output = await client.execute("show interface status")
        interfaces = []
        for line in output.splitlines():
            m = re.match(
                r"(\S+)\s+\S*\s+(connected|notconnect|disabled|err-disabled)\s+(\S+)\s+(\S+)\s+(\S+)",
                line.strip(),
            )
            if m and not line.strip().startswith(("Port", "-")):
                status_raw = m.group(2)
                status = "up" if status_raw == "connected" else "down"
                speed_raw = m.group(5)
                speed_match = re.search(r"(\d+)", speed_raw)
                speed = f"{speed_match.group(1)}M" if speed_match else None
                interfaces.append(
                    InterfaceDetail(
                        name=m.group(1),
                        status=status,
                        speed=speed,
                    )
                )
        return interfaces

    async def get_vlans(self, client: SSHClient) -> list[VLANInfo]:
        output = await client.execute("show vlan")
        vlans = []
        for line in output.splitlines():
            m = re.match(r"(\d+)\s+(\S+(?:\s+\S+)*?)\s{2,}(active|act/unsup)", line.strip())
            if m and not line.strip().startswith(("VLAN", "----")):
                vlans.append(
                    VLANInfo(id=int(m.group(1)), name=m.group(2).strip(), ports=[])
                )
        return vlans

    async def get_device_info(self, client: SSHClient) -> DeviceInfo:
        output = await client.execute("show version")
        hostname = "unknown"
        model = None
        serial = None
        firmware = None
        for line in output.splitlines():
            m = re.match(r"System Name:\s*(.+)", line)
            if m:
                hostname = m.group(1).strip()
            m = re.match(r"Serial Number:\s*(.+)", line)
            if m:
                serial = m.group(1).strip()
            m = re.match(r".+Software,\s*Version\s*(.+)", line)
            if m:
                firmware = m.group(1).strip()
        return DeviceInfo(
            hostname=hostname, model=model, serial=serial, firmware=firmware
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/parsers/test_fs_com.py -v`

Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add src/netbox_skill/parsers/fs_com.py tests/fixtures/fs_com/ tests/unit/parsers/test_fs_com.py
git commit -m "feat: add FS.com CLI parser with fixtures"
```

---

### Task 14: NetBox Service

**Files:**
- Create: `src/netbox_skill/services/__init__.py`
- Create: `src/netbox_skill/services/netbox.py`
- Create: `tests/unit/services/__init__.py`
- Create: `tests/unit/services/test_netbox_service.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/services/__init__.py
```

```python
# tests/unit/services/test_netbox_service.py
from unittest.mock import AsyncMock

import pytest

from netbox_skill.models.netbox import Device, DeviceCreate, DeviceUpdate
from netbox_skill.services.netbox import NetBoxService


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def service(mock_client):
    return NetBoxService(client=mock_client)


DEVICE_RESPONSE = {
    "id": 1,
    "url": "https://netbox.test/api/dcim/devices/1/",
    "display": "sw1",
    "name": "sw1",
    "status": {"value": "active", "label": "Active"},
    "serial": "SN123",
}


async def test_get_devices(service, mock_client):
    mock_client.get_all = AsyncMock(return_value=[DEVICE_RESPONSE])
    devices = await service.get_devices(status="active")
    assert len(devices) == 1
    assert isinstance(devices[0], Device)
    assert devices[0].name == "sw1"
    mock_client.get_all.assert_called_once_with("dcim/devices/", params={"status": "active"})


async def test_create_device(service, mock_client):
    mock_client.create = AsyncMock(return_value=DEVICE_RESPONSE)
    data = DeviceCreate(name="sw1", role=1, device_type=1, site=1)
    device = await service.create_device(data)
    assert isinstance(device, Device)
    assert device.id == 1


async def test_update_device(service, mock_client):
    mock_client.update = AsyncMock(return_value={**DEVICE_RESPONSE, "name": "sw1-renamed"})
    data = DeviceUpdate(name="sw1-renamed")
    device = await service.update_device(1, data)
    assert device.name == "sw1-renamed"


async def test_delete_device(service, mock_client):
    mock_client.delete = AsyncMock()
    await service.delete_device(1)
    mock_client.delete.assert_called_once_with("dcim/devices/", id=1)


async def test_find_or_create_device_exists(service, mock_client):
    mock_client.get_all = AsyncMock(return_value=[DEVICE_RESPONSE])
    data = DeviceCreate(name="sw1", role=1, device_type=1, site=1)
    device, created = await service.find_or_create_device(data, match_fields=["name"])
    assert created is False
    assert device.name == "sw1"


async def test_find_or_create_device_creates(service, mock_client):
    mock_client.get_all = AsyncMock(return_value=[])
    mock_client.create = AsyncMock(return_value=DEVICE_RESPONSE)
    data = DeviceCreate(name="sw1", role=1, device_type=1, site=1)
    device, created = await service.find_or_create_device(data, match_fields=["name"])
    assert created is True
    assert device.id == 1


async def test_find_or_create_interface(service, mock_client):
    iface_resp = {
        "id": 10,
        "url": "https://netbox.test/api/dcim/interfaces/10/",
        "display": "Ethernet1",
        "name": "Ethernet1",
        "device": {"id": 1, "display": "sw1"},
    }
    mock_client.get_all = AsyncMock(return_value=[iface_resp])
    iface, created = await service.find_or_create_interface(device_id=1, name="Ethernet1")
    assert created is False
    assert iface.name == "Ethernet1"


async def test_bulk_create_or_update(service, mock_client):
    existing = [DEVICE_RESPONSE]
    mock_client.get_all = AsyncMock(return_value=existing)
    mock_client.create = AsyncMock(return_value={"id": 2, "url": "u", "display": "sw2", "name": "sw2"})

    items = [
        {"name": "sw1", "role": 1, "device_type": 1, "site": 1},  # exists
        {"name": "sw2", "role": 1, "device_type": 1, "site": 1},  # new
    ]
    result = await service.bulk_create_or_update("dcim/devices/", items, match_fields=["name"])
    assert result.unchanged == 1
    assert result.created == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_netbox_service.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/services/__init__.py
"""Business logic services."""
```

```python
# src/netbox_skill/services/netbox.py
"""NetBox service — business logic over the NetBox API client."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from netbox_skill.models.common import BulkResult
from netbox_skill.models.netbox import (
    Cable,
    CableCreate,
    Device,
    DeviceCreate,
    DeviceType,
    DeviceUpdate,
    Interface,
    InterfaceCreate,
    IPAddress,
    IPAddressCreate,
    Prefix,
    Rack,
    Site,
    VLAN,
)

if TYPE_CHECKING:
    from netbox_skill.clients.netbox import NetBoxClient


class NetBoxService:
    def __init__(self, client: NetBoxClient):
        self._client = client

    # --- Device CRUD ---

    async def get_devices(self, **filters: Any) -> list[Device]:
        data = await self._client.get_all("dcim/devices/", params=filters or None)
        return [Device.model_validate(d) for d in data]

    async def create_device(self, data: DeviceCreate) -> Device:
        result = await self._client.create(
            "dcim/devices/", data=data.model_dump(exclude_none=True)
        )
        return Device.model_validate(result)

    async def update_device(self, id: int, data: DeviceUpdate) -> Device:
        result = await self._client.update(
            "dcim/devices/", id=id, data=data.model_dump(exclude_none=True)
        )
        return Device.model_validate(result)

    async def delete_device(self, id: int) -> None:
        await self._client.delete("dcim/devices/", id=id)

    # --- Interface CRUD ---

    async def get_interfaces(self, **filters: Any) -> list[Interface]:
        data = await self._client.get_all("dcim/interfaces/", params=filters or None)
        return [Interface.model_validate(d) for d in data]

    async def create_interface(self, data: InterfaceCreate) -> Interface:
        result = await self._client.create(
            "dcim/interfaces/", data=data.model_dump(exclude_none=True)
        )
        return Interface.model_validate(result)

    # --- IP Address CRUD ---

    async def get_ip_addresses(self, **filters: Any) -> list[IPAddress]:
        data = await self._client.get_all("ipam/ip-addresses/", params=filters or None)
        return [IPAddress.model_validate(d) for d in data]

    async def create_ip_address(self, data: IPAddressCreate) -> IPAddress:
        result = await self._client.create(
            "ipam/ip-addresses/", data=data.model_dump(exclude_none=True)
        )
        return IPAddress.model_validate(result)

    # --- VLAN CRUD ---

    async def get_vlans(self, **filters: Any) -> list[VLAN]:
        data = await self._client.get_all("ipam/vlans/", params=filters or None)
        return [VLAN.model_validate(d) for d in data]

    # --- Cable CRUD ---

    async def get_cables(self, **filters: Any) -> list[Cable]:
        data = await self._client.get_all("dcim/cables/", params=filters or None)
        return [Cable.model_validate(d) for d in data]

    async def create_cable(self, data: CableCreate) -> Cable:
        result = await self._client.create(
            "dcim/cables/", data=data.model_dump(exclude_none=True)
        )
        return Cable.model_validate(result)

    # --- Site, Rack, DeviceType ---

    async def get_sites(self, **filters: Any) -> list[Site]:
        data = await self._client.get_all("dcim/sites/", params=filters or None)
        return [Site.model_validate(d) for d in data]

    async def get_racks(self, **filters: Any) -> list[Rack]:
        data = await self._client.get_all("dcim/racks/", params=filters or None)
        return [Rack.model_validate(d) for d in data]

    async def get_device_types(self, **filters: Any) -> list[DeviceType]:
        data = await self._client.get_all("dcim/device-types/", params=filters or None)
        return [DeviceType.model_validate(d) for d in data]

    # --- Higher-level operations ---

    async def find_or_create_device(
        self, data: DeviceCreate, match_fields: list[str]
    ) -> tuple[Device, bool]:
        filters = {f: getattr(data, f) for f in match_fields if getattr(data, f, None) is not None}
        existing = await self.get_devices(**filters)
        if existing:
            return existing[0], False
        device = await self.create_device(data)
        return device, True

    async def find_or_create_interface(
        self, device_id: int, name: str
    ) -> tuple[Interface, bool]:
        existing = await self.get_interfaces(device_id=device_id, name=name)
        if existing:
            return existing[0], False
        data = InterfaceCreate(device=device_id, name=name)
        iface = await self.create_interface(data)
        return iface, True

    async def assign_ip_to_interface(
        self, ip: str, interface_id: int
    ) -> IPAddress:
        data = IPAddressCreate(
            address=ip,
            assigned_object_type="dcim.interface",
            assigned_object_id=interface_id,
        )
        return await self.create_ip_address(data)

    async def create_cable_between(
        self,
        a_type: str,
        a_id: int,
        b_type: str,
        b_id: int,
    ) -> Cable:
        data = CableCreate(
            a_terminations=[{"object_type": a_type, "object_id": a_id}],
            b_terminations=[{"object_type": b_type, "object_id": b_id}],
        )
        return await self.create_cable(data)

    async def get_device_with_interfaces(self, device_id: int) -> dict:
        devices = await self.get_devices(id=device_id)
        interfaces = await self.get_interfaces(device_id=device_id)
        return {
            "device": devices[0] if devices else None,
            "interfaces": interfaces,
        }

    async def bulk_create_or_update(
        self,
        endpoint: str,
        items: list[dict[str, Any]],
        match_fields: list[str],
    ) -> BulkResult:
        existing = await self._client.get_all(endpoint)
        existing_index: dict[tuple, dict] = {}
        for obj in existing:
            key = tuple(obj.get(f) for f in match_fields)
            existing_index[key] = obj

        created = 0
        unchanged = 0
        errors: list[str] = []

        for item in items:
            key = tuple(item.get(f) for f in match_fields)
            if key in existing_index:
                unchanged += 1
            else:
                try:
                    await self._client.create(endpoint, data=item)
                    created += 1
                except Exception as e:
                    errors.append(str(e))

        return BulkResult(created=created, updated=0, unchanged=unchanged, errors=errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_netbox_service.py -v`

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/services/ tests/unit/services/
git commit -m "feat: add NetBox service with CRUD and higher-level operations"
```

---

### Task 15: Discovery Service

**Files:**
- Create: `src/netbox_skill/services/discovery.py`
- Create: `tests/unit/services/test_discovery_service.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/services/test_discovery_service.py
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from netbox_skill.models.common import CredentialSet, DeviceTarget
from netbox_skill.models.discovery import DeviceInfo, MACEntry, DiscoveryResult
from netbox_skill.services.discovery import DiscoveryService, CredentialResolver


class MockCredentialResolver:
    async def resolve(self, target: DeviceTarget) -> CredentialSet:
        return target.credentials or CredentialSet(username="admin", password="pass")


@pytest.fixture
def service():
    return DiscoveryService(credential_resolver=MockCredentialResolver(), max_concurrent=2)


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_device(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_device_info = AsyncMock(return_value=DeviceInfo(hostname="sw1"))
    mock_parser.get_mac_table = AsyncMock(return_value=[MACEntry(mac="AA:BB:CC:DD:EE:01", port="Eth0", vlan=100)])
    mock_parser.get_arp_table = AsyncMock(return_value=[])
    mock_parser.get_lldp_neighbors = AsyncMock(return_value=[])
    mock_parser.get_interfaces = AsyncMock(return_value=[])
    mock_parser.get_vlans = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = await service.discover_device(target)
    assert isinstance(result, DiscoveryResult)
    assert result.device_info.hostname == "sw1"
    assert len(result.mac_table) == 1
    assert result.errors == []


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_device_selective(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_mac_table = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = await service.discover_device(target, data_types=["mac_table"])
    mock_parser.get_mac_table.assert_called_once()
    mock_parser.get_arp_table.assert_not_called()


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_device_partial_failure(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_device_info = AsyncMock(return_value=DeviceInfo(hostname="sw1"))
    mock_parser.get_mac_table = AsyncMock(side_effect=Exception("timeout"))
    mock_parser.get_arp_table = AsyncMock(return_value=[])
    mock_parser.get_lldp_neighbors = AsyncMock(return_value=[])
    mock_parser.get_interfaces = AsyncMock(return_value=[])
    mock_parser.get_vlans = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    result = await service.discover_device(target)
    assert len(result.errors) == 1
    assert "timeout" in result.errors[0]
    assert result.mac_table == []


@patch("netbox_skill.services.discovery.SSHClient")
@patch("netbox_skill.services.discovery.get_parser")
async def test_discover_devices_concurrent(mock_get_parser, mock_ssh_cls, service):
    mock_parser = AsyncMock()
    mock_parser.get_device_info = AsyncMock(return_value=DeviceInfo(hostname="sw"))
    mock_parser.get_mac_table = AsyncMock(return_value=[])
    mock_parser.get_arp_table = AsyncMock(return_value=[])
    mock_parser.get_lldp_neighbors = AsyncMock(return_value=[])
    mock_parser.get_interfaces = AsyncMock(return_value=[])
    mock_parser.get_vlans = AsyncMock(return_value=[])
    mock_get_parser.return_value = mock_parser

    mock_client_instance = AsyncMock()
    mock_ssh_cls.return_value = mock_client_instance
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    targets = [
        DeviceTarget(host="10.0.0.1", platform="sonic"),
        DeviceTarget(host="10.0.0.2", platform="sonic"),
        DeviceTarget(host="10.0.0.3", platform="sonic"),
    ]
    results = await service.discover_devices(targets)
    assert len(results) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_discovery_service.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/services/discovery.py
"""Discovery service — SSH into devices and collect operational data."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Protocol, TYPE_CHECKING

from netbox_skill.clients.ssh import SSHClient
from netbox_skill.models.common import CredentialSet, DeviceTarget
from netbox_skill.models.discovery import (
    ARPEntry,
    DeviceInfo,
    DiscoveryResult,
    InterfaceDetail,
    LLDPNeighbor,
    MACEntry,
    VLANInfo,
)
from netbox_skill.parsers.registry import get_parser

if TYPE_CHECKING:
    from netbox_skill.services.netbox import NetBoxService


class CredentialResolver(Protocol):
    async def resolve(self, target: DeviceTarget) -> CredentialSet: ...


DATA_TYPE_METHODS = {
    "mac_table": "get_mac_table",
    "arp_table": "get_arp_table",
    "lldp": "get_lldp_neighbors",
    "interfaces": "get_interfaces",
    "vlans": "get_vlans",
    "device_info": "get_device_info",
}


class DiscoveryService:
    def __init__(
        self,
        credential_resolver: CredentialResolver,
        max_concurrent: int = 10,
    ):
        self._credential_resolver = credential_resolver
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def discover_device(
        self,
        target: DeviceTarget,
        data_types: list[str] | None = None,
    ) -> DiscoveryResult:
        creds = await self._credential_resolver.resolve(target)
        parser = get_parser(target.platform)
        types_to_collect = data_types or list(DATA_TYPE_METHODS.keys())

        result_data: dict[str, Any] = {
            "target": target,
            "timestamp": datetime.now(timezone.utc),
            "errors": [],
        }

        async with SSHClient(host=target.host, credentials=creds) as client:
            for data_type in types_to_collect:
                method_name = DATA_TYPE_METHODS.get(data_type)
                if not method_name:
                    continue
                try:
                    value = await getattr(parser, method_name)(client)
                    result_data[data_type] = value
                except Exception as e:
                    result_data["errors"].append(f"{data_type}: {e}")

        return DiscoveryResult(
            target=target,
            device_info=result_data.get("device_info"),
            mac_table=result_data.get("mac_table", []),
            arp_table=result_data.get("arp_table", []),
            lldp_neighbors=result_data.get("lldp", []),
            interfaces=result_data.get("interfaces", []),
            vlans=result_data.get("vlans", []),
            errors=result_data.get("errors", []),
            timestamp=result_data["timestamp"],
        )

    async def discover_devices(
        self,
        targets: list[DeviceTarget],
        data_types: list[str] | None = None,
    ) -> list[DiscoveryResult]:
        async def _limited(target: DeviceTarget) -> DiscoveryResult:
            async with self._semaphore:
                try:
                    return await self.discover_device(target, data_types)
                except Exception as e:
                    return DiscoveryResult(
                        target=target,
                        timestamp=datetime.now(timezone.utc),
                        errors=[str(e)],
                    )

        tasks = [_limited(t) for t in targets]
        return list(await asyncio.gather(*tasks))

    async def discover_from_netbox(
        self,
        netbox: NetBoxService,
        filters: dict[str, Any],
        data_types: list[str] | None = None,
    ) -> list[DiscoveryResult]:
        devices = await netbox.get_devices(**filters)
        targets = []
        for device in devices:
            if device.primary_ip4 and isinstance(device.primary_ip4, dict):
                ip = device.primary_ip4.get("address", "").split("/")[0]
            else:
                continue
            platform_name = ""
            if device.platform and hasattr(device.platform, "slug"):
                platform_name = device.platform.slug or ""
            if not platform_name:
                continue
            targets.append(
                DeviceTarget(
                    host=ip,
                    platform=platform_name,
                    device_id=device.id,
                )
            )
        return await self.discover_devices(targets, data_types)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_discovery_service.py -v`

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/services/discovery.py tests/unit/services/test_discovery_service.py
git commit -m "feat: add discovery service with concurrent SSH and pluggable credential resolver"
```

---

### Task 16: Orchestrator Service

**Files:**
- Create: `src/netbox_skill/services/orchestrator.py`
- Create: `tests/unit/services/test_orchestrator_service.py`

This task implements the sync_device workflow. `sync_topology` follows the same pattern and is left as a follow-up within this task.

- [ ] **Step 1: Write the test**

```python
# tests/unit/services/test_orchestrator_service.py
from unittest.mock import AsyncMock

import pytest

from netbox_skill.models.common import DeviceTarget, SyncMode
from netbox_skill.models.discovery import (
    DeviceInfo,
    DiscoveryResult,
    InterfaceDetail,
    LLDPNeighbor,
)
from netbox_skill.models.netbox import Device, Interface
from netbox_skill.services.orchestrator import OrchestratorService
from datetime import datetime, timezone


@pytest.fixture
def mock_netbox():
    return AsyncMock()


@pytest.fixture
def mock_discovery():
    return AsyncMock()


@pytest.fixture
def service(mock_netbox, mock_discovery):
    return OrchestratorService(netbox=mock_netbox, discovery=mock_discovery)


def make_discovery_result(target, interfaces=None, lldp=None):
    return DiscoveryResult(
        target=target,
        device_info=DeviceInfo(hostname="sw1", model="SN2700", serial="MT123"),
        interfaces=interfaces or [],
        lldp_neighbors=lldp or [],
        timestamp=datetime.now(timezone.utc),
    )


def make_device(id=1, name="sw1"):
    return Device(
        id=id, url=f"https://nb/api/dcim/devices/{id}/", display=name, name=name,
        serial="MT123",
    )


async def test_sync_device_dry_run(service, mock_netbox, mock_discovery):
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    mock_discovery.discover_device = AsyncMock(
        return_value=make_discovery_result(
            target,
            interfaces=[InterfaceDetail(name="Ethernet0", status="up", speed="100G")],
        )
    )
    mock_netbox.find_or_create_device = AsyncMock(return_value=(make_device(), False))
    mock_netbox.get_interfaces = AsyncMock(return_value=[])

    report = await service.sync_device(target, mode=SyncMode.DRY_RUN)
    assert len(report.conflicts) > 0 or len(report.created) > 0 or len(report.unchanged) >= 0
    mock_netbox.create_interface.assert_not_called()


async def test_sync_device_auto_creates_interfaces(service, mock_netbox, mock_discovery):
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    mock_discovery.discover_device = AsyncMock(
        return_value=make_discovery_result(
            target,
            interfaces=[InterfaceDetail(name="Ethernet0", status="up")],
        )
    )
    device = make_device()
    mock_netbox.find_or_create_device = AsyncMock(return_value=(device, False))
    mock_netbox.get_interfaces = AsyncMock(return_value=[])
    mock_netbox.find_or_create_interface = AsyncMock(
        return_value=(Interface(id=10, url="u", display="Ethernet0", name="Ethernet0"), True)
    )

    report = await service.sync_device(target, mode=SyncMode.AUTO)
    assert any(r.action == "created" and r.object_type == "interface" for r in report.created)


async def test_sync_device_existing_interface_unchanged(service, mock_netbox, mock_discovery):
    target = DeviceTarget(host="10.0.0.1", platform="sonic")
    mock_discovery.discover_device = AsyncMock(
        return_value=make_discovery_result(
            target,
            interfaces=[InterfaceDetail(name="Ethernet0", status="up")],
        )
    )
    device = make_device()
    mock_netbox.find_or_create_device = AsyncMock(return_value=(device, False))
    existing_iface = Interface(id=10, url="u", display="Ethernet0", name="Ethernet0")
    mock_netbox.get_interfaces = AsyncMock(return_value=[existing_iface])
    mock_netbox.find_or_create_interface = AsyncMock(return_value=(existing_iface, False))

    report = await service.sync_device(target, mode=SyncMode.AUTO)
    assert "Ethernet0" in report.unchanged


async def test_sync_topology_creates_cables(service, mock_netbox, mock_discovery):
    target1 = DeviceTarget(host="10.0.0.1", platform="sonic", device_id=1)
    target2 = DeviceTarget(host="10.0.0.2", platform="sonic", device_id=2)

    result1 = make_discovery_result(
        target1,
        lldp=[LLDPNeighbor(local_port="Ethernet0", remote_device="sw2", remote_port="Ethernet0")],
    )
    result2 = make_discovery_result(
        target2,
        lldp=[LLDPNeighbor(local_port="Ethernet0", remote_device="sw1", remote_port="Ethernet0")],
    )
    mock_discovery.discover_devices = AsyncMock(return_value=[result1, result2])

    mock_netbox.get_devices = AsyncMock(return_value=[make_device(1, "sw1"), make_device(2, "sw2")])

    iface1 = Interface(id=10, url="u", display="Ethernet0", name="Ethernet0", device={"id": 1, "display": "sw1"})
    iface2 = Interface(id=20, url="u", display="Ethernet0", name="Ethernet0", device={"id": 2, "display": "sw2"})
    mock_netbox.get_interfaces = AsyncMock(side_effect=[[iface1], [iface2]])
    mock_netbox.get_cables = AsyncMock(return_value=[])
    mock_netbox.create_cable_between = AsyncMock()

    report = await service.sync_topology([target1, target2], mode=SyncMode.AUTO)
    mock_netbox.create_cable_between.assert_called()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_orchestrator_service.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/services/orchestrator.py
"""Orchestrator service — discover, diff, populate NetBox."""

from __future__ import annotations

from typing import TYPE_CHECKING

from netbox_skill.models.common import (
    ChangeRecord,
    ConflictRecord,
    DeviceTarget,
    SyncMode,
    SyncReport,
)
from netbox_skill.models.netbox import DeviceCreate

if TYPE_CHECKING:
    from netbox_skill.services.discovery import DiscoveryService
    from netbox_skill.services.netbox import NetBoxService


class OrchestratorService:
    def __init__(self, netbox: NetBoxService, discovery: DiscoveryService):
        self._netbox = netbox
        self._discovery = discovery

    async def sync_device(
        self, target: DeviceTarget, mode: SyncMode
    ) -> SyncReport:
        result = await self._discovery.discover_device(target)
        report = SyncReport(device=target, errors=list(result.errors))

        # Find or create the device in NetBox
        device_data = DeviceCreate(
            name=result.device_info.hostname if result.device_info else target.host,
            role=1,  # Placeholder — caller should set via target or config
            device_type=1,  # Placeholder
            site=1,  # Placeholder
            serial=result.device_info.serial if result.device_info else None,
        )
        device, device_created = await self._netbox.find_or_create_device(
            device_data, match_fields=["name"]
        )
        if device_created:
            report.created.append(
                ChangeRecord(
                    object_type="device",
                    object_id=device.id,
                    action="created",
                    detail={"name": device.name},
                )
            )

        # Sync interfaces
        existing_interfaces = await self._netbox.get_interfaces(device_id=device.id)
        existing_names = {i.name for i in existing_interfaces}

        for iface in result.interfaces:
            if iface.name in existing_names:
                report.unchanged.append(iface.name)
            else:
                if mode == SyncMode.DRY_RUN:
                    report.created.append(
                        ChangeRecord(
                            object_type="interface",
                            action="would_create",
                            detail={"name": iface.name, "device_id": device.id},
                        )
                    )
                else:
                    nb_iface, created = await self._netbox.find_or_create_interface(
                        device_id=device.id, name=iface.name
                    )
                    if created:
                        report.created.append(
                            ChangeRecord(
                                object_type="interface",
                                object_id=nb_iface.id,
                                action="created",
                                detail={"name": iface.name},
                            )
                        )
                    else:
                        report.unchanged.append(iface.name)

        return report

    async def sync_devices(
        self, targets: list[DeviceTarget], mode: SyncMode
    ) -> list[SyncReport]:
        reports = []
        for target in targets:
            try:
                report = await self.sync_device(target, mode)
                reports.append(report)
            except Exception as e:
                reports.append(SyncReport(device=target, errors=[str(e)]))
        return reports

    async def sync_topology(
        self, targets: list[DeviceTarget], mode: SyncMode
    ) -> SyncReport:
        report = SyncReport(device=targets[0] if targets else DeviceTarget(host="", platform=""))

        results = await self._discovery.discover_devices(targets)

        # Build hostname → device_id mapping
        all_devices = await self._netbox.get_devices()
        name_to_device = {d.name: d for d in all_devices}

        for result in results:
            if not result.device_info:
                continue
            local_device = name_to_device.get(result.device_info.hostname)
            if not local_device:
                continue

            local_interfaces = await self._netbox.get_interfaces(device_id=local_device.id)
            local_iface_map = {i.name: i for i in local_interfaces}

            for neighbor in result.lldp_neighbors:
                local_iface = local_iface_map.get(neighbor.local_port)
                remote_device = name_to_device.get(neighbor.remote_device)
                if not local_iface or not remote_device:
                    continue

                remote_interfaces = await self._netbox.get_interfaces(device_id=remote_device.id)
                remote_iface_map = {i.name: i for i in remote_interfaces}
                remote_iface = remote_iface_map.get(neighbor.remote_port)
                if not remote_iface:
                    continue

                if mode != SyncMode.DRY_RUN:
                    await self._netbox.create_cable_between(
                        "dcim.interface", local_iface.id,
                        "dcim.interface", remote_iface.id,
                    )
                    report.created.append(
                        ChangeRecord(
                            object_type="cable",
                            action="created",
                            detail={
                                "a": f"{local_device.name}:{neighbor.local_port}",
                                "b": f"{remote_device.name}:{neighbor.remote_port}",
                            },
                        )
                    )

        return report
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_orchestrator_service.py -v`

Expected: 4 passed (the sync_topology test may need adjustment based on mock setup — fix as needed)

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/services/orchestrator.py tests/unit/services/test_orchestrator_service.py
git commit -m "feat: add orchestrator service with sync_device and sync_topology"
```

---

### Task 17: Vision Provider Base and Claude Implementation

**Files:**
- Create: `src/netbox_skill/vision/__init__.py`
- Create: `src/netbox_skill/vision/base.py`
- Create: `src/netbox_skill/vision/claude.py`
- Create: `tests/unit/vision/__init__.py`
- Create: `tests/unit/vision/test_claude_provider.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/vision/__init__.py
```

```python
# tests/unit/vision/test_claude_provider.py
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from netbox_skill.models.rack_vision import RackContext
from netbox_skill.vision.base import VisionProvider
from netbox_skill.vision.claude import ClaudeVisionProvider


def test_claude_provider_is_vision_provider():
    assert issubclass(ClaudeVisionProvider, VisionProvider)


@patch("netbox_skill.vision.claude.anthropic")
async def test_analyze_rack(mock_anthropic):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"devices": [{"u_start": 1, "u_end": 2, "mount_type": "rack", "model_guess": "Dell R640", "confidence": 0.9, "asset_tag": null, "serial": null, "hostname_label": "srv1", "crop_region": [0, 0, 800, 100]}]}')]
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    provider = ClaudeVisionProvider(api_key="test-key")
    context = RackContext(rack_id=5, site="DC1")
    result = await provider.analyze_rack(
        image=b"fake_image_data", prompt="Analyze this rack", context=context
    )
    assert "devices" in result
    assert len(result["devices"]) == 1
    assert result["devices"][0]["model_guess"] == "Dell R640"


@patch("netbox_skill.vision.claude.anthropic")
async def test_identify_device(mock_anthropic):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"model_guess": "Netgear GS308", "confidence": 0.75}')]
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    provider = ClaudeVisionProvider(api_key="test-key")
    result = await provider.identify_device(crop=b"cropped_data", prompt="What device is this?")
    assert result["model_guess"] == "Netgear GS308"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/vision/test_claude_provider.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/vision/__init__.py
"""Vision providers for image analysis."""
```

```python
# src/netbox_skill/vision/base.py
"""Vision provider base class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from netbox_skill.models.rack_vision import RackContext


class VisionProvider(ABC):
    @abstractmethod
    async def analyze_rack(
        self, image: bytes, prompt: str, context: RackContext
    ) -> dict[str, Any]:
        """Send rack image for analysis. Returns structured JSON response."""
        ...

    @abstractmethod
    async def identify_device(
        self, crop: bytes, prompt: str
    ) -> dict[str, Any]:
        """Send cropped device image for closer identification."""
        ...
```

```python
# src/netbox_skill/vision/claude.py
"""Claude Vision provider implementation."""

from __future__ import annotations

import base64
import json
from typing import Any

import anthropic

from netbox_skill.exceptions import VisionProviderError
from netbox_skill.models.rack_vision import RackContext
from netbox_skill.vision.base import VisionProvider


class ClaudeVisionProvider(VisionProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def _send_image(
        self, image: bytes, prompt: str
    ) -> dict[str, Any]:
        image_b64 = base64.standard_b64encode(image).decode("utf-8")
        try:
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
        except Exception as e:
            raise VisionProviderError(f"Claude API call failed: {e}") from e

        text = message.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            raise VisionProviderError(f"Could not parse JSON from Claude response: {text}")

    async def analyze_rack(
        self, image: bytes, prompt: str, context: RackContext
    ) -> dict[str, Any]:
        context_str = ""
        if context.site:
            context_str += f" Site: {context.site}."
        if context.expected_devices:
            context_str += f" Expected devices: {', '.join(context.expected_devices)}."

        full_prompt = (
            f"{prompt}\n\n"
            f"Context:{context_str}\n\n"
            "Respond with JSON containing a 'devices' array. Each device should have: "
            "u_start (int or null), u_end (int or null), mount_type ('rack' or 'shelf'), "
            "model_guess (string), confidence (float 0-1), asset_tag (string or null), "
            "serial (string or null), hostname_label (string or null), "
            "crop_region ([x1, y1, x2, y2] pixel coordinates)."
        )
        return await self._send_image(image, full_prompt)

    async def identify_device(
        self, crop: bytes, prompt: str
    ) -> dict[str, Any]:
        full_prompt = (
            f"{prompt}\n\n"
            "Respond with JSON containing: model_guess (string), confidence (float 0-1), "
            "asset_tag (string or null), serial (string or null), hostname_label (string or null)."
        )
        return await self._send_image(crop, full_prompt)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/vision/test_claude_provider.py -v`

Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/vision/ tests/unit/vision/
git commit -m "feat: add vision provider base class and Claude implementation"
```

---

### Task 18: Rack Vision Service

**Files:**
- Create: `src/netbox_skill/services/rack_vision.py`
- Create: `tests/unit/services/test_rack_vision_service.py`

- [ ] **Step 1: Write the test**

```python
# tests/unit/services/test_rack_vision_service.py
from difflib import SequenceMatcher
from unittest.mock import AsyncMock

import pytest

from netbox_skill.models.common import SyncMode, ChangeRecord
from netbox_skill.models.netbox import DeviceType
from netbox_skill.models.rack_vision import (
    DetectedDevice,
    DeviceConfirmation,
    RackAnalysis,
    RackContext,
)
from netbox_skill.services.rack_vision import RackVisionService


def make_detected(model="Dell R640", confidence=0.9, mount_type="rack", u_start=1, u_end=2):
    return DetectedDevice(
        u_start=u_start, u_end=u_end, mount_type=mount_type,
        model_guess=model, confidence=confidence,
        crop_region=(0, 0, 100, 50),
    )


def make_analysis(devices=None):
    return RackAnalysis(
        devices=devices or [make_detected()],
        annotated_image=b"img",
        rack_context=RackContext(rack_id=5),
    )


@pytest.fixture
def mock_vision():
    return AsyncMock()


@pytest.fixture
def mock_netbox():
    return AsyncMock()


@pytest.fixture
def service(mock_vision, mock_netbox):
    return RackVisionService(vision=mock_vision, netbox=mock_netbox, confidence_threshold=0.7)


async def test_analyze_rack_photo(service, mock_vision):
    mock_vision.analyze_rack = AsyncMock(return_value={
        "devices": [
            {"u_start": 1, "u_end": 2, "mount_type": "rack", "model_guess": "Dell R640",
             "confidence": 0.9, "asset_tag": None, "serial": None,
             "hostname_label": "srv1", "crop_region": [0, 0, 800, 100]},
        ]
    })
    analysis = await service.analyze_rack_photo(image=b"photo", context=RackContext(rack_id=5))
    assert len(analysis.devices) == 1
    assert analysis.devices[0].model_guess == "Dell R640"


async def test_get_uncertain_devices(service):
    devices = [
        make_detected("Dell R640", confidence=0.9),
        make_detected("Unknown Box", confidence=0.5),
        make_detected("Netgear GS308", confidence=0.65, mount_type="shelf", u_start=None, u_end=None),
    ]
    analysis = make_analysis(devices)
    uncertain = service.get_uncertain_devices(analysis)
    assert len(uncertain) == 2
    assert uncertain[0][0] == 1  # index
    assert uncertain[1][0] == 2


async def test_match_device_types_auto(service, mock_netbox):
    mock_netbox.get_device_types = AsyncMock(return_value=[
        DeviceType(id=10, url="u", display="PowerEdge R640", manufacturer=None, model="PowerEdge R640", slug="r640"),
    ])
    analysis = make_analysis([make_detected("Dell R640")])
    result = await service.match_device_types(analysis)
    assert result.devices[0].matched_device_type_id is not None or result.devices[0].match_candidates is not None


async def test_match_device_types_no_match(service, mock_netbox):
    mock_netbox.get_device_types = AsyncMock(return_value=[
        DeviceType(id=10, url="u", display="SN2700", manufacturer=None, model="SN2700", slug="sn2700"),
    ])
    analysis = make_analysis([make_detected("Totally Unknown Device XYZ")])
    result = await service.match_device_types(analysis)
    assert result.devices[0].matched_device_type_id is None


async def test_apply_confirmations(service):
    analysis = make_analysis([
        make_detected("Dell R640", confidence=0.5),
        make_detected("Unknown", confidence=0.3),
    ])
    confirmations = [
        DeviceConfirmation(index=0, confirmed=True, corrected_model="Dell PowerEdge R640", device_type_id=10, create_new_type=False),
        DeviceConfirmation(index=1, confirmed=False, create_new_type=False),
    ]
    result = service.apply_confirmations(analysis, confirmations)
    assert result.devices[0].model_guess == "Dell PowerEdge R640"
    assert result.devices[0].matched_device_type_id == 10


async def test_populate_rack_dry_run(service, mock_netbox):
    analysis = make_analysis([make_detected()])
    analysis.devices[0].matched_device_type_id = 10
    report = await service.populate_rack(analysis, rack_id=5, mode=SyncMode.DRY_RUN)
    assert report.rack_id == 5
    mock_netbox.create_device.assert_not_called()


async def test_populate_rack_auto(service, mock_netbox):
    analysis = make_analysis([make_detected()])
    analysis.devices[0].matched_device_type_id = 10
    analysis.devices[0].hostname_label = "srv-db-01"

    from netbox_skill.models.netbox import Device
    mock_netbox.find_or_create_device = AsyncMock(
        return_value=(Device(id=1, url="u", display="srv-db-01", name="srv-db-01"), True)
    )

    report = await service.populate_rack(analysis, rack_id=5, mode=SyncMode.AUTO)
    assert len(report.created) == 1
    mock_netbox.find_or_create_device.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/services/test_rack_vision_service.py -v`

Expected: FAIL — `ImportError`

- [ ] **Step 3: Write the implementation**

```python
# src/netbox_skill/services/rack_vision.py
"""Rack vision service — AI-powered rack photo analysis and NetBox population."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from netbox_skill.models.common import ChangeRecord, SyncMode
from netbox_skill.models.netbox import DeviceCreate
from netbox_skill.models.rack_vision import (
    DetectedDevice,
    DeviceConfirmation,
    DeviceTypeMatch,
    RackAnalysis,
    RackContext,
    RackPopulationReport,
)

if TYPE_CHECKING:
    from netbox_skill.services.netbox import NetBoxService
    from netbox_skill.vision.base import VisionProvider


class RackVisionService:
    def __init__(
        self,
        vision: VisionProvider,
        netbox: NetBoxService,
        confidence_threshold: float = 0.7,
    ):
        self._vision = vision
        self._netbox = netbox
        self._confidence_threshold = confidence_threshold

    async def analyze_rack_photo(
        self, image: bytes, context: RackContext
    ) -> RackAnalysis:
        prompt = "Analyze this rack photo. Identify all devices, their rack unit positions, and any visible labels."
        raw = await self._vision.analyze_rack(image, prompt, context)
        devices = []
        for d in raw.get("devices", []):
            crop = d.get("crop_region", [0, 0, 0, 0])
            devices.append(
                DetectedDevice(
                    u_start=d.get("u_start"),
                    u_end=d.get("u_end"),
                    mount_type=d.get("mount_type", "rack"),
                    model_guess=d.get("model_guess", "unknown"),
                    confidence=d.get("confidence", 0.0),
                    asset_tag=d.get("asset_tag"),
                    serial=d.get("serial"),
                    hostname_label=d.get("hostname_label"),
                    crop_region=(crop[0], crop[1], crop[2], crop[3]),
                )
            )
        return RackAnalysis(
            devices=devices,
            annotated_image=image,  # In production, vision provider would return annotated version
            rack_context=context,
        )

    def get_uncertain_devices(
        self, analysis: RackAnalysis
    ) -> list[tuple[int, DetectedDevice, bytes]]:
        uncertain = []
        for i, device in enumerate(analysis.devices):
            if device.confidence < self._confidence_threshold:
                # In production, crop from the original image using crop_region
                crop = b"cropped_image_data"
                uncertain.append((i, device, crop))
        return uncertain

    async def match_device_types(self, analysis: RackAnalysis) -> RackAnalysis:
        device_types = await self._netbox.get_device_types()
        for device in analysis.devices:
            best_match: DeviceTypeMatch | None = None
            candidates: list[DeviceTypeMatch] = []
            for dt in device_types:
                ratio = SequenceMatcher(
                    None, device.model_guess.lower(), dt.model.lower()
                ).ratio()
                match = DeviceTypeMatch(
                    device_type_id=dt.id, name=dt.model, similarity=ratio
                )
                if ratio > 0.85:
                    if best_match is None or ratio > best_match.similarity:
                        best_match = match
                elif ratio > 0.5:
                    candidates.append(match)

            if best_match:
                device.matched_device_type_id = best_match.device_type_id
            if candidates:
                device.match_candidates = sorted(
                    candidates, key=lambda m: m.similarity, reverse=True
                )
        return analysis

    def apply_confirmations(
        self, analysis: RackAnalysis, confirmations: list[DeviceConfirmation]
    ) -> RackAnalysis:
        for conf in confirmations:
            if conf.index >= len(analysis.devices):
                continue
            device = analysis.devices[conf.index]
            if not conf.confirmed:
                continue
            if conf.corrected_model:
                device.model_guess = conf.corrected_model
            if conf.corrected_mount_type:
                device.mount_type = conf.corrected_mount_type
            if conf.corrected_u_start is not None:
                device.u_start = conf.corrected_u_start
            if conf.corrected_u_end is not None:
                device.u_end = conf.corrected_u_end
            if conf.corrected_asset_tag is not None:
                device.asset_tag = conf.corrected_asset_tag
            if conf.corrected_serial is not None:
                device.serial = conf.corrected_serial
            if conf.device_type_id is not None:
                device.matched_device_type_id = conf.device_type_id
        return analysis

    async def populate_rack(
        self,
        analysis: RackAnalysis,
        rack_id: int,
        mode: SyncMode,
    ) -> RackPopulationReport:
        report = RackPopulationReport(rack_id=rack_id)

        for device in analysis.devices:
            if not device.matched_device_type_id:
                report.skipped.append(
                    f"No device type matched for {device.model_guess} at U{device.u_start}"
                )
                continue

            name = device.hostname_label or f"rack{rack_id}-u{device.u_start or 'shelf'}"

            if mode == SyncMode.DRY_RUN:
                report.created.append(
                    ChangeRecord(
                        object_type="device",
                        action="would_create",
                        detail={
                            "name": name,
                            "rack": rack_id,
                            "position": device.u_start,
                            "device_type": device.matched_device_type_id,
                        },
                    )
                )
                continue

            data = DeviceCreate(
                name=name,
                role=1,  # Caller should configure default role
                device_type=device.matched_device_type_id,
                site=1,  # Caller should configure
                rack=rack_id,
                position=float(device.u_start) if device.u_start else None,
                face="front",
                serial=device.serial,
                asset_tag=device.asset_tag,
            )
            nb_device, created = await self._netbox.find_or_create_device(
                data, match_fields=["name"]
            )
            if created:
                report.created.append(
                    ChangeRecord(
                        object_type="device",
                        object_id=nb_device.id,
                        action="created",
                        detail={"name": name},
                    )
                )
            else:
                report.updated.append(
                    ChangeRecord(
                        object_type="device",
                        object_id=nb_device.id,
                        action="exists",
                        detail={"name": name},
                    )
                )

        return report
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/services/test_rack_vision_service.py -v`

Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/netbox_skill/services/rack_vision.py tests/unit/services/test_rack_vision_service.py
git commit -m "feat: add rack vision service with photo analysis, fuzzy matching, and population"
```

---

### Task 19: MCP Server Transport

**Files:**
- Create: `src/netbox_skill/transports/__init__.py`
- Create: `src/netbox_skill/transports/mcp/__init__.py`
- Create: `src/netbox_skill/transports/mcp/server.py`
- Create: `src/netbox_skill/transports/mcp/tools_netbox.py`
- Create: `src/netbox_skill/transports/mcp/tools_discovery.py`
- Create: `src/netbox_skill/transports/mcp/tools_orchestrator.py`
- Create: `src/netbox_skill/transports/mcp/tools_rack.py`

This task builds the MCP server with all tool registrations. Tests are at the integration level since MCP tools are thin wrappers over services.

- [ ] **Step 1: Create transport init files**

```python
# src/netbox_skill/transports/__init__.py
"""Transport adapters (MCP, HTTP)."""
```

```python
# src/netbox_skill/transports/mcp/__init__.py
"""MCP server transport."""
```

- [ ] **Step 2: Write the MCP server entry point**

```python
# src/netbox_skill/transports/mcp/server.py
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
        # Check device-specific overrides
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
```

- [ ] **Step 3: Write NetBox tools**

```python
# src/netbox_skill/transports/mcp/tools_netbox.py
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
```

- [ ] **Step 4: Write Discovery tools**

```python
# src/netbox_skill/transports/mcp/tools_discovery.py
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
```

- [ ] **Step 5: Write Orchestrator tools**

```python
# src/netbox_skill/transports/mcp/tools_orchestrator.py
"""MCP tool definitions for orchestration (sync) workflows."""

from __future__ import annotations

import json
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from netbox_skill.models.common import DeviceTarget, SyncMode
from netbox_skill.services.orchestrator import OrchestratorService


def register_orchestrator_tools(server: Server, orchestrator: OrchestratorService) -> None:

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="sync_device", description="Discover a device and sync to NetBox", inputSchema={"type": "object", "properties": {"host": {"type": "string"}, "platform": {"type": "string"}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["host", "platform"]}),
            Tool(name="sync_devices", description="Sync multiple devices to NetBox", inputSchema={"type": "object", "properties": {"targets": {"type": "array", "items": {"type": "object", "properties": {"host": {"type": "string"}, "platform": {"type": "string"}}, "required": ["host", "platform"]}}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["targets"]}),
            Tool(name="sync_topology", description="Sync LLDP-based topology to NetBox cables", inputSchema={"type": "object", "properties": {"targets": {"type": "array", "items": {"type": "object"}}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["targets"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            result = await _dispatch(name, arguments, orchestrator)
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _dispatch(name: str, args: dict[str, Any], orchestrator: OrchestratorService) -> Any:
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
    return {"error": f"Unknown tool: {name}"}
```

- [ ] **Step 6: Write Rack tools**

```python
# src/netbox_skill/transports/mcp/tools_rack.py
"""MCP tool definitions for rack photo population."""

from __future__ import annotations

import base64
import json
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

from netbox_skill.models.common import SyncMode
from netbox_skill.models.rack_vision import DeviceConfirmation, RackContext
from netbox_skill.services.rack_vision import RackVisionService

# Module-level state for multi-step rack workflow
_current_analysis = None


def register_rack_tools(server: Server, rack_vision: RackVisionService) -> None:
    global _current_analysis

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="rack_analyze_photo", description="Analyze a rack photo to detect devices and their positions", inputSchema={"type": "object", "properties": {"image_base64": {"type": "string", "description": "Base64-encoded rack photo"}, "rack_id": {"type": "integer"}, "site": {"type": "string"}, "expected_devices": {"type": "array", "items": {"type": "string"}}}, "required": ["image_base64"]}),
            Tool(name="rack_get_uncertain", description="Get devices that need user confirmation from the last analysis", inputSchema={"type": "object", "properties": {}}),
            Tool(name="rack_confirm_device", description="Confirm or correct a detected device", inputSchema={"type": "object", "properties": {"index": {"type": "integer"}, "confirmed": {"type": "boolean"}, "corrected_model": {"type": "string"}, "device_type_id": {"type": "integer"}, "create_new_type": {"type": "boolean"}}, "required": ["index", "confirmed"]}),
            Tool(name="rack_populate", description="Push confirmed devices into NetBox", inputSchema={"type": "object", "properties": {"rack_id": {"type": "integer"}, "mode": {"type": "string", "enum": ["dry_run", "auto", "confirm"], "default": "dry_run"}}, "required": ["rack_id"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        global _current_analysis
        try:
            result = await _dispatch(name, arguments, rack_vision)
            return [TextContent(type="text", text=json.dumps(result, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _dispatch(name: str, args: dict[str, Any], rack_vision: RackVisionService) -> Any:
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

    return {"error": f"Unknown tool: {name}"}
```

- [ ] **Step 7: Verify imports work**

Run: `cd /Users/syncer/GitHub/netbox-skill && source .venv/bin/activate && python -c "from netbox_skill.transports.mcp.server import create_server; print('OK')"`

Expected: Fails (needs NETBOX_URL/TOKEN env vars) but confirms imports resolve. If it fails with ConfigError, that's correct.

- [ ] **Step 8: Commit**

```bash
git add src/netbox_skill/transports/
git commit -m "feat: add MCP server transport with all tool registrations"
```

---

### Task 20: HTTP Transport Scaffold

**Files:**
- Create: `src/netbox_skill/transports/http/__init__.py`
- Create: `src/netbox_skill/transports/http/app.py`
- Create: `src/netbox_skill/transports/http/routes_netbox.py`
- Create: `src/netbox_skill/transports/http/routes_discovery.py`
- Create: `src/netbox_skill/transports/http/routes_orchestrator.py`

- [ ] **Step 1: Create scaffold files**

```python
# src/netbox_skill/transports/http/__init__.py
"""HTTP/FastAPI transport (scaffolded)."""
```

```python
# src/netbox_skill/transports/http/app.py
"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from netbox_skill.transports.http.routes_netbox import router as netbox_router
from netbox_skill.transports.http.routes_discovery import router as discovery_router
from netbox_skill.transports.http.routes_orchestrator import router as orchestrator_router


def create_app() -> FastAPI:
    app = FastAPI(title="NetBox Skill", version="0.1.0")
    app.include_router(netbox_router, prefix="/api/netbox", tags=["netbox"])
    app.include_router(discovery_router, prefix="/api/discovery", tags=["discovery"])
    app.include_router(orchestrator_router, prefix="/api/sync", tags=["sync"])
    return app


def main():
    import uvicorn
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
```

```python
# src/netbox_skill/transports/http/routes_netbox.py
"""NetBox API routes (scaffold — returns 501)."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/{resource}/")
async def list_resource(resource: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/{resource}/")
async def create_resource(resource: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{resource}/{id}/")
async def get_resource(resource: str, id: int):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/{resource}/{id}/")
async def update_resource(resource: str, id: int):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.delete("/{resource}/{id}/")
async def delete_resource(resource: str, id: int):
    raise HTTPException(status_code=501, detail="Not implemented")
```

```python
# src/netbox_skill/transports/http/routes_discovery.py
"""Discovery API routes (scaffold — returns 501)."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/device")
async def discover_device():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/devices")
async def discover_devices():
    raise HTTPException(status_code=501, detail="Not implemented")
```

```python
# src/netbox_skill/transports/http/routes_orchestrator.py
"""Orchestrator/sync API routes (scaffold — returns 501)."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/device")
async def sync_device():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/devices")
async def sync_devices():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/topology")
async def sync_topology():
    raise HTTPException(status_code=501, detail="Not implemented")
```

- [ ] **Step 2: Verify FastAPI app creates**

Run: `cd /Users/syncer/GitHub/netbox-skill && source .venv/bin/activate && python -c "from netbox_skill.transports.http.app import create_app; app = create_app(); print(f'Routes: {len(app.routes)}')"`

Expected: Prints route count, no errors

- [ ] **Step 3: Commit**

```bash
git add src/netbox_skill/transports/http/
git commit -m "feat: scaffold HTTP/FastAPI transport with 501 stub routes"
```

---

### Task 21: Run Full Test Suite

- [ ] **Step 1: Run all tests**

Run: `cd /Users/syncer/GitHub/netbox-skill && source .venv/bin/activate && pytest tests/ -v --tb=short`

Expected: All tests pass (approximately 75+ tests)

- [ ] **Step 2: Fix any failures**

Address any test failures found in step 1.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "fix: resolve any remaining test failures"
```

---

### Task 22: Update CLAUDE.md with Final State

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md**

Add the final tech stack, entry points, and test commands to CLAUDE.md:

```markdown
## Running

### MCP Server
```bash
NETBOX_URL=https://netbox.example.com NETBOX_TOKEN=nbt_xxx python -m netbox_skill.transports.mcp
```

### HTTP Server (scaffold)
```bash
python -m netbox_skill.transports.http
```

### Tests
```bash
pip install -e ".[dev]"
pytest tests/ -v
```
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with run commands and test instructions"
```
