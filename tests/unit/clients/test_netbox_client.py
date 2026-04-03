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
    # Register the more-specific route first so respx matches it before the general one
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
