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
