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
