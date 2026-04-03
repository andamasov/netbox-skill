"""Discovery API routes (scaffold — returns 501)."""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/device")
async def discover_device():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/devices")
async def discover_devices():
    raise HTTPException(status_code=501, detail="Not implemented")
