# tests/unit/test_models_rack_vision.py
from netbox_skill.models.common import ChangeRecord
from netbox_skill.models.rack_vision import (
    RackContext,
    DetectedDevice,
    DeviceTypeMatch,
    RackAnalysis,
    DeviceConfirmation,
    RackPopulationReport,
)


def test_rack_context_minimal():
    ctx = RackContext()
    assert ctx.rack_id is None
    assert ctx.site is None
    assert ctx.expected_devices is None


def test_rack_context_full():
    ctx = RackContext(rack_id=5, site="DC1", expected_devices=["SN2700", "M4300"])
    assert ctx.rack_id == 5
    assert len(ctx.expected_devices) == 2


def test_detected_device_rack_mounted():
    dev = DetectedDevice(
        u_start=10,
        u_end=11,
        mount_type="rack",
        model_guess="Dell PowerEdge R640",
        confidence=0.92,
        asset_tag="ASSET001",
        serial="SVC123",
        hostname_label="srv-db-01",
        crop_region=(100, 200, 800, 300),
    )
    assert dev.mount_type == "rack"
    assert dev.u_start == 10
    assert dev.confidence == 0.92


def test_detected_device_shelf():
    dev = DetectedDevice(
        u_start=None,
        u_end=None,
        mount_type="shelf",
        model_guess="Netgear GS308",
        confidence=0.65,
        crop_region=(100, 500, 400, 550),
    )
    assert dev.mount_type == "shelf"
    assert dev.u_start is None
    assert dev.matched_device_type_id is None
    assert dev.match_candidates is None


def test_device_type_match():
    m = DeviceTypeMatch(device_type_id=42, name="SN2700-32C", similarity=0.88)
    assert m.similarity == 0.88


def test_detected_device_with_matches():
    dev = DetectedDevice(
        mount_type="rack",
        model_guess="SN2700",
        confidence=0.8,
        crop_region=(0, 0, 100, 100),
        matched_device_type_id=42,
        match_candidates=[
            DeviceTypeMatch(device_type_id=42, name="SN2700-32C", similarity=0.9),
            DeviceTypeMatch(device_type_id=43, name="SN2700-64C", similarity=0.85),
        ],
    )
    assert dev.matched_device_type_id == 42
    assert len(dev.match_candidates) == 2


def test_rack_analysis():
    analysis = RackAnalysis(
        devices=[
            DetectedDevice(
                u_start=1,
                u_end=2,
                mount_type="rack",
                model_guess="R640",
                confidence=0.95,
                crop_region=(0, 0, 100, 100),
            )
        ],
        annotated_image=b"fake_image_data",
        rack_context=RackContext(rack_id=5),
    )
    assert len(analysis.devices) == 1
    assert analysis.errors == []


def test_device_confirmation():
    conf = DeviceConfirmation(
        index=0,
        confirmed=True,
        corrected_model="Dell R640",
        device_type_id=10,
        create_new_type=False,
    )
    assert conf.confirmed is True
    assert conf.corrected_model == "Dell R640"


def test_device_confirmation_reject():
    conf = DeviceConfirmation(index=2, confirmed=False, create_new_type=False)
    assert conf.confirmed is False


def test_rack_population_report():
    report = RackPopulationReport(
        rack_id=5,
        created=[ChangeRecord(object_type="device", object_id=10, action="created", detail={"name": "srv1"})],
        updated=[],
        skipped=["Unknown device at U20"],
        errors=[],
    )
    assert report.rack_id == 5
    assert len(report.created) == 1
    assert len(report.skipped) == 1
