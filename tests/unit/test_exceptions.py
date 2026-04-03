from netbox_skill.exceptions import (
    NetBoxSkillError,
    NetBoxClientError,
    NetBoxAuthError,
    NetBoxNotFoundError,
    NetBoxValidationError,
    NetBoxServerError,
    DeviceError,
    DeviceConnectionError,
    CommandError,
    UnknownPlatformError,
    VisionError,
    VisionProviderError,
    ImageProcessingError,
    ConfigError,
)


def test_exception_hierarchy():
    assert issubclass(NetBoxClientError, NetBoxSkillError)
    assert issubclass(NetBoxAuthError, NetBoxClientError)
    assert issubclass(NetBoxNotFoundError, NetBoxClientError)
    assert issubclass(NetBoxValidationError, NetBoxClientError)
    assert issubclass(NetBoxServerError, NetBoxClientError)
    assert issubclass(DeviceError, NetBoxSkillError)
    assert issubclass(DeviceConnectionError, DeviceError)
    assert issubclass(CommandError, DeviceError)
    assert issubclass(UnknownPlatformError, DeviceError)
    assert issubclass(VisionError, NetBoxSkillError)
    assert issubclass(VisionProviderError, VisionError)
    assert issubclass(ImageProcessingError, VisionError)
    assert issubclass(ConfigError, NetBoxSkillError)


def test_netbox_client_error_stores_status_and_body():
    err = NetBoxClientError(status_code=400, body={"detail": "bad"}, message="fail")
    assert err.status_code == 400
    assert err.body == {"detail": "bad"}
    assert "fail" in str(err)


def test_netbox_validation_error_stores_field_errors():
    err = NetBoxValidationError(
        status_code=400,
        body={"name": ["This field is required."]},
        message="Validation failed",
    )
    assert err.field_errors == {"name": ["This field is required."]}


def test_unknown_platform_error_stores_platform():
    err = UnknownPlatformError("mikrotik")
    assert err.platform == "mikrotik"
    assert "mikrotik" in str(err)
