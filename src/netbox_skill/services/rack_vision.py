"""Rack vision service — AI-powered rack photo analysis and NetBox population."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from netbox_skill.models.common import ChangeRecord, SyncMode
from netbox_skill.models.netbox import DeviceCreate
from netbox_skill.models.rack_vision import (
    DetectedDevice,
    DeviceConfirmation,
    DeviceTypeMatch,
    RackAnalysis,
    RackContext,
    RackPopulationReport,
)

if TYPE_CHECKING:
    from netbox_skill.services.netbox import NetBoxService
    from netbox_skill.vision.base import VisionProvider


class RackVisionService:
    def __init__(
        self,
        vision: VisionProvider,
        netbox: NetBoxService,
        confidence_threshold: float = 0.7,
    ):
        self._vision = vision
        self._netbox = netbox
        self._confidence_threshold = confidence_threshold

    async def analyze_rack_photo(
        self, image: bytes, context: RackContext
    ) -> RackAnalysis:
        prompt = "Analyze this rack photo. Identify all devices, their rack unit positions, and any visible labels."
        raw = await self._vision.analyze_rack(image, prompt, context)
        devices = []
        for d in raw.get("devices", []):
            crop = d.get("crop_region", [0, 0, 0, 0])
            devices.append(
                DetectedDevice(
                    u_start=d.get("u_start"),
                    u_end=d.get("u_end"),
                    mount_type=d.get("mount_type", "rack"),
                    model_guess=d.get("model_guess", "unknown"),
                    confidence=d.get("confidence", 0.0),
                    asset_tag=d.get("asset_tag"),
                    serial=d.get("serial"),
                    hostname_label=d.get("hostname_label"),
                    crop_region=(crop[0], crop[1], crop[2], crop[3]),
                )
            )
        return RackAnalysis(
            devices=devices,
            annotated_image=image,
            rack_context=context,
        )

    def get_uncertain_devices(
        self, analysis: RackAnalysis
    ) -> list[tuple[int, DetectedDevice, bytes]]:
        uncertain = []
        for i, device in enumerate(analysis.devices):
            if device.confidence < self._confidence_threshold:
                crop = b"cropped_image_data"
                uncertain.append((i, device, crop))
        return uncertain

    async def match_device_types(self, analysis: RackAnalysis) -> RackAnalysis:
        device_types = await self._netbox.get_device_types()
        for device in analysis.devices:
            best_match: DeviceTypeMatch | None = None
            candidates: list[DeviceTypeMatch] = []
            for dt in device_types:
                ratio = SequenceMatcher(
                    None, device.model_guess.lower(), dt.model.lower()
                ).ratio()
                match = DeviceTypeMatch(
                    device_type_id=dt.id, name=dt.model, similarity=ratio
                )
                if ratio > 0.85:
                    if best_match is None or ratio > best_match.similarity:
                        best_match = match
                elif ratio > 0.5:
                    candidates.append(match)

            if best_match:
                device.matched_device_type_id = best_match.device_type_id
            if candidates:
                device.match_candidates = sorted(
                    candidates, key=lambda m: m.similarity, reverse=True
                )
        return analysis

    def apply_confirmations(
        self, analysis: RackAnalysis, confirmations: list[DeviceConfirmation]
    ) -> RackAnalysis:
        for conf in confirmations:
            if conf.index >= len(analysis.devices):
                continue
            device = analysis.devices[conf.index]
            if not conf.confirmed:
                continue
            if conf.corrected_model:
                device.model_guess = conf.corrected_model
            if conf.corrected_mount_type:
                device.mount_type = conf.corrected_mount_type
            if conf.corrected_u_start is not None:
                device.u_start = conf.corrected_u_start
            if conf.corrected_u_end is not None:
                device.u_end = conf.corrected_u_end
            if conf.corrected_asset_tag is not None:
                device.asset_tag = conf.corrected_asset_tag
            if conf.corrected_serial is not None:
                device.serial = conf.corrected_serial
            if conf.device_type_id is not None:
                device.matched_device_type_id = conf.device_type_id
        return analysis

    async def populate_rack(
        self,
        analysis: RackAnalysis,
        rack_id: int,
        mode: SyncMode,
    ) -> RackPopulationReport:
        report = RackPopulationReport(rack_id=rack_id)

        for device in analysis.devices:
            if not device.matched_device_type_id:
                report.skipped.append(
                    f"No device type matched for {device.model_guess} at U{device.u_start}"
                )
                continue

            name = device.hostname_label or f"rack{rack_id}-u{device.u_start or 'shelf'}"

            if mode == SyncMode.DRY_RUN:
                report.created.append(
                    ChangeRecord(
                        object_type="device",
                        action="would_create",
                        detail={
                            "name": name,
                            "rack": rack_id,
                            "position": device.u_start,
                            "device_type": device.matched_device_type_id,
                        },
                    )
                )
                continue

            data = DeviceCreate(
                name=name,
                role=1,
                device_type=device.matched_device_type_id,
                site=1,
                rack=rack_id,
                position=float(device.u_start) if device.u_start else None,
                face="front",
                serial=device.serial,
                asset_tag=device.asset_tag,
            )
            nb_device, created = await self._netbox.find_or_create_device(
                data, match_fields=["name"]
            )
            if created:
                report.created.append(
                    ChangeRecord(
                        object_type="device",
                        object_id=nb_device.id,
                        action="created",
                        detail={"name": name},
                    )
                )
            else:
                report.updated.append(
                    ChangeRecord(
                        object_type="device",
                        object_id=nb_device.id,
                        action="exists",
                        detail={"name": name},
                    )
                )

        return report
