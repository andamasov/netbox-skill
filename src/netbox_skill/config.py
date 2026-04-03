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
