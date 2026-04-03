from difflib import SequenceMatcher
from unittest.mock import AsyncMock

import pytest

from netbox_skill.models.common import SyncMode, ChangeRecord
from netbox_skill.models.netbox import DeviceType
from netbox_skill.models.rack_vision import (
    DetectedDevice,
    DeviceConfirmation,
    RackAnalysis,
    RackContext,
)
from netbox_skill.services.rack_vision import RackVisionService


def make_detected(model="Dell R640", confidence=0.9, mount_type="rack", u_start=1, u_end=2):
    return DetectedDevice(
        u_start=u_start, u_end=u_end, mount_type=mount_type,
        model_guess=model, confidence=confidence,
        crop_region=(0, 0, 100, 50),
    )


def make_analysis(devices=None):
    return RackAnalysis(
        devices=devices or [make_detected()],
        annotated_image=b"img",
        rack_context=RackContext(rack_id=5),
    )


@pytest.fixture
def mock_vision():
    return AsyncMock()


@pytest.fixture
def mock_netbox():
    return AsyncMock()


@pytest.fixture
def service(mock_vision, mock_netbox):
    return RackVisionService(vision=mock_vision, netbox=mock_netbox, confidence_threshold=0.7)


async def test_analyze_rack_photo(service, mock_vision):
    mock_vision.analyze_rack = AsyncMock(return_value={
        "devices": [
            {"u_start": 1, "u_end": 2, "mount_type": "rack", "model_guess": "Dell R640",
             "confidence": 0.9, "asset_tag": None, "serial": None,
             "hostname_label": "srv1", "crop_region": [0, 0, 800, 100]},
        ]
    })
    analysis = await service.analyze_rack_photo(image=b"photo", context=RackContext(rack_id=5))
    assert len(analysis.devices) == 1
    assert analysis.devices[0].model_guess == "Dell R640"


async def test_get_uncertain_devices(service):
    devices = [
        make_detected("Dell R640", confidence=0.9),
        make_detected("Unknown Box", confidence=0.5),
        make_detected("Netgear GS308", confidence=0.65, mount_type="shelf", u_start=None, u_end=None),
    ]
    analysis = make_analysis(devices)
    uncertain = service.get_uncertain_devices(analysis)
    assert len(uncertain) == 2
    assert uncertain[0][0] == 1  # index
    assert uncertain[1][0] == 2


async def test_match_device_types_auto(service, mock_netbox):
    mock_netbox.get_device_types = AsyncMock(return_value=[
        DeviceType(id=10, url="u", display="PowerEdge R640", manufacturer=None, model="PowerEdge R640", slug="r640"),
    ])
    analysis = make_analysis([make_detected("Dell R640")])
    result = await service.match_device_types(analysis)
    assert result.devices[0].matched_device_type_id is not None or result.devices[0].match_candidates is not None


async def test_match_device_types_no_match(service, mock_netbox):
    mock_netbox.get_device_types = AsyncMock(return_value=[
        DeviceType(id=10, url="u", display="SN2700", manufacturer=None, model="SN2700", slug="sn2700"),
    ])
    analysis = make_analysis([make_detected("Totally Unknown Device XYZ")])
    result = await service.match_device_types(analysis)
    assert result.devices[0].matched_device_type_id is None


async def test_apply_confirmations(service):
    analysis = make_analysis([
        make_detected("Dell R640", confidence=0.5),
        make_detected("Unknown", confidence=0.3),
    ])
    confirmations = [
        DeviceConfirmation(index=0, confirmed=True, corrected_model="Dell PowerEdge R640", device_type_id=10, create_new_type=False),
        DeviceConfirmation(index=1, confirmed=False, create_new_type=False),
    ]
    result = service.apply_confirmations(analysis, confirmations)
    assert result.devices[0].model_guess == "Dell PowerEdge R640"
    assert result.devices[0].matched_device_type_id == 10


async def test_populate_rack_dry_run(service, mock_netbox):
    analysis = make_analysis([make_detected()])
    analysis.devices[0].matched_device_type_id = 10
    report = await service.populate_rack(analysis, rack_id=5, mode=SyncMode.DRY_RUN)
    assert report.rack_id == 5
    mock_netbox.create_device.assert_not_called()


async def test_populate_rack_auto(service, mock_netbox):
    analysis = make_analysis([make_detected()])
    analysis.devices[0].matched_device_type_id = 10
    analysis.devices[0].hostname_label = "srv-db-01"

    from netbox_skill.models.netbox import Device
    mock_netbox.find_or_create_device = AsyncMock(
        return_value=(Device(id=1, url="u", display="srv-db-01", name="srv-db-01"), True)
    )

    report = await service.populate_rack(analysis, rack_id=5, mode=SyncMode.AUTO)
    assert len(report.created) == 1
    mock_netbox.find_or_create_device.assert_called_once()
