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
