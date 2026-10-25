"""Pytest suite for UserProfile and service operations.
Tests will execute during Kepler's automated verification phase.
"""
import pytest
from service.models import UserProfile


def test_valid_user_creation():
    user = UserProfile(
        user_id=1,
        username="CloudNative",
        email="sre@example.com",
        bio="Kubernetes & SRE",
    )
    assert user.user_id == 1
    assert user.username == "cloudnative"  # Validated and lowercased
    assert user.is_active is True


def test_username_too_short():
    with pytest.raises(Exception):
        UserProfile(user_id=2, username="ab", email="short@example.com")


def test_model_serialization_dict():
    user = UserProfile(
        user_id=3,
        username="RubixKube",
        email="kepler@rubixkube.ai",
        bio="Kepler SRE AI IDE",
    )
    # Checks serialization
    data = user.dict() if hasattr(user, "dict") else user.model_dump()
    assert isinstance(data, dict)
    assert data["user_id"] == 3
    assert data["username"] == "rubixkube"


def test_model_configuration_presence():
    # In Pydantic v1: class Config exists on class
    # In Pydantic v2: model_config dictionary exists
    has_v1_config = hasattr(UserProfile, "Config")
    has_v2_config = hasattr(UserProfile, "model_config")
    assert has_v1_config or has_v2_config, "Model must have configuration defined"
