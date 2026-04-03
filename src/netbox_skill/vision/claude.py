"""Claude Vision provider implementation."""

from __future__ import annotations

import base64
import json
from typing import Any

import anthropic

from netbox_skill.exceptions import VisionProviderError
from netbox_skill.models.rack_vision import RackContext
from netbox_skill.vision.base import VisionProvider


class ClaudeVisionProvider(VisionProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def _send_image(
        self, image: bytes, prompt: str
    ) -> dict[str, Any]:
        image_b64 = base64.standard_b64encode(image).decode("utf-8")
        try:
            message = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
        except Exception as e:
            raise VisionProviderError(f"Claude API call failed: {e}") from e

        text = message.content[0].text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            raise VisionProviderError(f"Could not parse JSON from Claude response: {text}")

    async def analyze_rack(
        self, image: bytes, prompt: str, context: RackContext
    ) -> dict[str, Any]:
        context_str = ""
        if context.site:
            context_str += f" Site: {context.site}."
        if context.expected_devices:
            context_str += f" Expected devices: {', '.join(context.expected_devices)}."

        full_prompt = (
            f"{prompt}\n\n"
            f"Context:{context_str}\n\n"
            "Respond with JSON containing a 'devices' array. Each device should have: "
            "u_start (int or null), u_end (int or null), mount_type ('rack' or 'shelf'), "
            "model_guess (string), confidence (float 0-1), asset_tag (string or null), "
            "serial (string or null), hostname_label (string or null), "
            "crop_region ([x1, y1, x2, y2] pixel coordinates)."
        )
        return await self._send_image(image, full_prompt)

    async def identify_device(
        self, crop: bytes, prompt: str
    ) -> dict[str, Any]:
        full_prompt = (
            f"{prompt}\n\n"
            "Respond with JSON containing: model_guess (string), confidence (float 0-1), "
            "asset_tag (string or null), serial (string or null), hostname_label (string or null)."
        )
        return await self._send_image(crop, full_prompt)
