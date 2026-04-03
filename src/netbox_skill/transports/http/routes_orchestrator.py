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
