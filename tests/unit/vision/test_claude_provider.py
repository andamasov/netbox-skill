from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from netbox_skill.models.rack_vision import RackContext
from netbox_skill.vision.base import VisionProvider
from netbox_skill.vision.claude import ClaudeVisionProvider


def test_claude_provider_is_vision_provider():
    assert issubclass(ClaudeVisionProvider, VisionProvider)


@patch("netbox_skill.vision.claude.anthropic")
async def test_analyze_rack(mock_anthropic):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"devices": [{"u_start": 1, "u_end": 2, "mount_type": "rack", "model_guess": "Dell R640", "confidence": 0.9, "asset_tag": null, "serial": null, "hostname_label": "srv1", "crop_region": [0, 0, 800, 100]}]}')]
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    provider = ClaudeVisionProvider(api_key="test-key")
    context = RackContext(rack_id=5, site="DC1")
    result = await provider.analyze_rack(
        image=b"fake_image_data", prompt="Analyze this rack", context=context
    )
    assert "devices" in result
    assert len(result["devices"]) == 1
    assert result["devices"][0]["model_guess"] == "Dell R640"


@patch("netbox_skill.vision.claude.anthropic")
async def test_identify_device(mock_anthropic):
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"model_guess": "Netgear GS308", "confidence": 0.75}')]
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    provider = ClaudeVisionProvider(api_key="test-key")
    result = await provider.identify_device(crop=b"cropped_data", prompt="What device is this?")
    assert result["model_guess"] == "Netgear GS308"
