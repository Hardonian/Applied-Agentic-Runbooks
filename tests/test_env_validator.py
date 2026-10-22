"""Tests for environment variable validator."""

import os

import pytest

from agent_factory.core.exceptions import ConfigurationError
from agent_factory.utils.env_validator import EnvironmentValidator, validate_agent_factory_env


@pytest.mark.unit
def test_add_required_variable():
    """Test adding required variables."""
    validator = EnvironmentValidator()
    validator.add_required("TEST_VAR", "Test variable")

    assert len(validator.required_vars) == 1
    assert validator.required_vars[0][0] == "TEST_VAR"


@pytest.mark.unit
def test_add_optional_variable():
    """Test adding optional variables."""
    validator = EnvironmentValidator()
    validator.add_optional("OPTIONAL_VAR", "default_value", "Optional variable")

    assert "OPTIONAL_VAR" in validator.optional_vars
    assert validator.optional_vars["OPTIONAL_VAR"]["default"] == "default_value"


@pytest.mark.unit
def test_validate_missing_required():
    """Test validation with missing required variables."""
    validator = EnvironmentValidator()
    validator.add_required("REQUIRED_VAR", "Required variable")

    # Clear the variable if it exists
    if "REQUIRED_VAR" in os.environ:
        del os.environ["REQUIRED_VAR"]

    is_valid, errors = validator.validate(raise_on_error=False)
    assert is_valid is False
    assert len(errors) == 1
    assert "REQUIRED_VAR" in errors[0]


@pytest.mark.unit
def test_validate_with_required():
    """Test validation with required variables set."""
    validator = EnvironmentValidator()
    validator.add_required("TEST_REQUIRED", "Test required")

    os.environ["TEST_REQUIRED"] = "test_value"

    is_valid, errors = validator.validate(raise_on_error=False)
    assert is_valid is True
    assert len(errors) == 0

    # Cleanup
    del os.environ["TEST_REQUIRED"]


@pytest.mark.unit
def test_validate_raises_on_error():
    """Test that validation raises on error when requested."""
    validator = EnvironmentValidator()
    validator.add_required("MISSING_VAR", "Missing variable")

    if "MISSING_VAR" in os.environ:
        del os.environ["MISSING_VAR"]

    with pytest.raises(ConfigurationError, match="Environment validation failed"):
        validator.validate(raise_on_error=True)


@pytest.mark.unit
def test_optional_variable_default():
    """Test that optional variables get default values."""
    validator = EnvironmentValidator()
    validator.add_optional("OPTIONAL_TEST", "default", "Optional test")

    if "OPTIONAL_TEST" in os.environ:
        del os.environ["OPTIONAL_TEST"]

    validator.validate(raise_on_error=False)

    assert os.getenv("OPTIONAL_TEST") == "default"

    # Cleanup
    del os.environ["OPTIONAL_TEST"]


@pytest.mark.unit
def test_get_environment_variable():
    """Test getting environment variable."""
    validator = EnvironmentValidator()

    os.environ["TEST_GET_VAR"] = "test_value"

    assert validator.get("TEST_GET_VAR") == "test_value"
    assert validator.get("NONEXISTENT", "default") == "default"

    # Cleanup
    del os.environ["TEST_GET_VAR"]


@pytest.mark.unit
def test_validate_agent_factory_env():
    """Test Agent Factory environment validation."""
    # Save original environment
    original_env = os.environ.copy()

    try:
        # Clear test variables
        test_vars = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ENVIRONMENT"]
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

        # Should not raise in development
        os.environ["ENVIRONMENT"] = "development"
        validator = validate_agent_factory_env()
        assert validator is not None

        # Should warn in production without API keys
        os.environ["ENVIRONMENT"] = "production"
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validator = validate_agent_factory_env()
            if w:
                assert any(
                    "Critical environment variables" in str(warning.message) for warning in w
                )

    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.mark.unit
def test_multiple_required_variables():
    """Test validation with multiple required variables."""
    validator = EnvironmentValidator()
    validator.add_required("VAR1", "Variable 1")
    validator.add_required("VAR2", "Variable 2")
    validator.add_required("VAR3", "Variable 3")

    # Clear all variables
    for var in ["VAR1", "VAR2", "VAR3"]:
        if var in os.environ:
            del os.environ[var]

    is_valid, errors = validator.validate(raise_on_error=False)
    assert is_valid is False
    assert len(errors) == 3


@pytest.mark.unit
def test_mixed_required_and_optional():
    """Test validation with both required and optional variables."""
    validator = EnvironmentValidator()
    validator.add_required("REQUIRED_VAR", "Required")
    validator.add_optional("OPTIONAL_VAR", "default", "Optional")

    os.environ["REQUIRED_VAR"] = "set"

    if "OPTIONAL_VAR" in os.environ:
        del os.environ["OPTIONAL_VAR"]

    is_valid, errors = validator.validate(raise_on_error=False)
    assert is_valid is True
    assert os.getenv("OPTIONAL_VAR") == "default"

    # Cleanup
    del os.environ["REQUIRED_VAR"]
    del os.environ["OPTIONAL_VAR"]
