# tests/unit/test_models_common.py
from netbox_skill.models.common import (
    CredentialSet,
    DeviceTarget,
    SyncMode,
    ChangeRecord,
    ConflictRecord,
    SyncReport,
    BulkResult,
)


def test_credential_set_password_only():
    creds = CredentialSet(username="admin", password="secret")
    assert creds.username == "admin"
    assert creds.password == "secret"
    assert creds.ssh_key_path is None


def test_credential_set_key_only():
    creds = CredentialSet(username="admin", ssh_key_path="/path/to/key")
    assert creds.password is None
    assert creds.ssh_key_path == "/path/to/key"


def test_device_target_minimal():
    target = DeviceTarget(host="192.168.1.1", platform="netgear")
    assert target.host == "192.168.1.1"
    assert target.platform == "netgear"
    assert target.credentials is None
    assert target.device_id is None


def test_device_target_with_credentials():
    creds = CredentialSet(username="admin", password="pass")
    target = DeviceTarget(
        host="10.0.0.1", platform="sonic", credentials=creds, device_id=42
    )
    assert target.credentials.username == "admin"
    assert target.device_id == 42


def test_sync_mode_values():
    assert SyncMode.DRY_RUN == "dry_run"
    assert SyncMode.AUTO == "auto"
    assert SyncMode.CONFIRM == "confirm"


def test_change_record():
    rec = ChangeRecord(
        object_type="device", object_id=5, action="created", detail={"name": "sw1"}
    )
    assert rec.object_type == "device"
    assert rec.action == "created"


def test_conflict_record():
    conflict = ConflictRecord(
        object_type="interface",
        field="speed",
        netbox_value="1000",
        discovered_value="10000",
    )
    assert conflict.field == "speed"


def test_sync_report_empty():
    target = DeviceTarget(host="1.1.1.1", platform="netgear")
    report = SyncReport(device=target)
    assert report.created == []
    assert report.updated == []
    assert report.unchanged == []
    assert report.conflicts == []
    assert report.errors == []


def test_bulk_result():
    result = BulkResult(created=3, updated=1, unchanged=10, errors=["fail"])
    assert result.created == 3
    assert result.errors == ["fail"]
