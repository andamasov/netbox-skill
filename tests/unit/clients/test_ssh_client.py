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
