"""Tests for security sanitization."""

import pytest

from agent_factory.security.sanitization import sanitize_input, sanitize_output


@pytest.mark.unit
def test_sanitize_input_basic():
    """Test basic input sanitization."""
    result = sanitize_input("test input")
    assert result == "test input"


@pytest.mark.unit
def test_sanitize_input_html():
    """Test HTML sanitization."""
    result = sanitize_input("<script>alert('xss')</script>")
    assert "<script>" not in result


@pytest.mark.unit
def test_sanitize_input_sql():
    """Test SQL injection pattern removal."""
    result = sanitize_input("'; DROP TABLE users; --")
    assert "DROP" not in result or "TABLE" not in result


@pytest.mark.unit
def test_sanitize_output_dict():
    """Test sanitizing dictionary output."""
    data = {"text": "<script>alert('xss')</script>", "number": 123}
    result = sanitize_output(data)
    assert "<script>" not in result["text"]
    assert result["number"] == 123


@pytest.mark.unit
def test_sanitize_output_list():
    """Test sanitizing list output."""
    data = ["<script>alert('xss')</script>", "normal text"]
    result = sanitize_output(data)
    assert "<script>" not in result[0]
    assert result[1] == "normal text"
