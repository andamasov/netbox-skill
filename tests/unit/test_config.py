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
