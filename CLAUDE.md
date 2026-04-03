# NetBox Skill

## Project Overview

Full-featured network infrastructure service for NetBox integration and network device discovery. Exposes functionality via MCP server transport, with architecture supporting future REST API and CLI transports.

## Target NetBox

- NetBox Community v4.5.6 (Docker 4.0.2)
- REST API base: `https://<host>/api/`
- Auth: Bearer token (`Authorization: Bearer nbt_<key>.<token>`)
- OpenAPI schema: `/api/schema/`

## Architecture

```
Transport Layer (MCP Server / future REST API / future CLI)
        |
Service Layer (transport-agnostic business logic)
  - NetBox Service (CRUD against NetBox REST API)
  - Discovery Service (SSH into switches, pull operational data)
        |
Client/Parser Layer
  - NetBox Client (typed HTTP client for NetBox REST API)
  - Device Parsers (pluggable per-vendor SSH/CLI parsers)
```

Core principle: the service layer contains all business logic. Transports are thin adapters.

## Two Functional Domains

### Part 1 — NetBox API Integration

CRUD operations against NetBox REST API. Priority endpoint groups:

**DCIM** (`/api/dcim/`): devices, interfaces, sites, locations, racks, cables, device-types, manufacturers, platforms, device-roles, console-ports, power-ports, front/rear-ports, module-bays, device-bays, inventory-items, mac-addresses, virtual-chassis

**IPAM** (`/api/ipam/`): ip-addresses, prefixes, vlans, vlan-groups, vrfs, aggregates, rirs, roles, asns, services, ip-ranges

**Circuits** (`/api/circuits/`): providers, circuits, circuit-types, circuit-terminations

**Tenancy** (`/api/tenancy/`): tenants, tenant-groups, contacts, contact-roles

**Virtualization** (`/api/virtualization/`): clusters, cluster-types, virtual-machines, interfaces, virtual-disks

**Extras** (`/api/extras/`): tags, custom-fields, config-contexts, webhooks, event-rules, journal-entries

### Part 2 — Device Discovery and Query

SSH/CLI-based operational data collection from network switches to discover topology and populate NetBox.

**Target devices (initial):**
- Netgear managed switches
- FS.com switches (Broadcom-based CLI)
- Mellanox SN2700 running SONiC

**Data to collect:**
- MAC address tables (MAC-to-port mapping)
- ARP tables (IP-to-MAC resolution)
- LLDP/CDP neighbors (switch-to-switch topology)
- Interface details (status, speed, description, type, MTU)
- VLAN assignments (which VLANs on which ports)
- Device info (hostname, model, serial number, firmware version)

**Design requirement:** Pluggable parser architecture — adding a new vendor means adding a new parser module without changing service logic.

### Orchestration

Combined workflows: discover from devices -> diff against NetBox -> populate/update NetBox.

## NetBox API Reference

### Authentication
- v2 tokens (recommended): `Authorization: Bearer nbt_<key>.<token>`
- v1 tokens (legacy): `Authorization: Token <token>`
- Tokens: per-user, optional expiration, can be read-only, IP-restricted
- Provision endpoint: `POST /api/users/tokens/provision/`

### CRUD Pattern
- `GET /api/<app>/<model>/` — list with filtering/pagination
- `POST /api/<app>/<model>/` — create (single or bulk via JSON array)
- `GET /api/<app>/<model>/{id}/` — retrieve
- `PUT /api/<app>/<model>/{id}/` — full update
- `PATCH /api/<app>/<model>/{id}/` — partial update
- `DELETE /api/<app>/<model>/{id}/` — delete (returns 204)

### Filtering
- Query params: `?status=active&region=europe`
- Lookup expressions: `__lt`, `__gt`, `__ic` (contains), `__isw` (starts with), `__iew` (ends with), `__regex`, `__empty`, `__n` (not equal)
- Multiple values = OR: `?region=a&region=b`
- Custom fields: `?cf_<name>=<value>`
- Ordering: `?ordering=name` or `?ordering=-name`

### Pagination
- Response: `{ "count": N, "next": "url", "previous": "url", "results": [...] }`
- Default page size: 50, max: 1000
- Control: `?limit=100&offset=200`
- Field selection: `?fields=id,name,status` or `?brief=true`

### Bulk Operations
- Bulk create: `POST` JSON array to list endpoint
- Bulk update: `PUT`/`PATCH` JSON array of `{"id": N, ...}` to list endpoint
- Bulk delete: `DELETE` JSON array of `{"id": N}` to list endpoint
- All-or-none semantics (atomic)

### Response Format
- Every object: `id`, `url`, `display`, `created`, `last_updated`
- Choice fields: `{"value": "...", "label": "..."}`
- Related objects: brief nested with `id`, `url`, `display`, `name`/`slug`
- Custom fields in `custom_fields` dict
- Headers: `API-Version`, `X-Request-ID`

### Special Endpoints
- Status: `GET /api/status/` (version, hostname, plugins, workers)
- Auth check: `GET /api/authentication-check/`
- Available IPs: `GET /api/ipam/prefixes/{id}/available-ips/`
- Available prefixes: `GET /api/ipam/prefixes/{id}/available-prefixes/`
- Available VLANs: `GET /api/ipam/vlan-groups/{id}/available-vlans/`

### GraphQL
- Read-only at `/graphql/`
- Same token auth as REST

## Tech Stack

To be determined during design phase. Prior work in this repo used TypeScript with Node.js.

## Repository

- GitHub: https://github.com/andamasov/netbox-skill
- Main branch: master
- Feature branch: feature/implement-mcp-server
