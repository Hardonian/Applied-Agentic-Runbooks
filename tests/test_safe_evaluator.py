"""Tests for safe expression evaluator."""

import pytest

from agent_factory.utils.safe_evaluator import SafeEvaluator, safe_evaluate


@pytest.mark.unit
def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    assert safe_evaluate("2 + 2") == 4
    assert safe_evaluate("10 - 5") == 5
    assert safe_evaluate("3 * 4") == 12
    assert safe_evaluate("15 / 3") == 5.0
    assert safe_evaluate("2 ** 3") == 8
    assert safe_evaluate("10 % 3") == 1


@pytest.mark.unit
def test_comparisons():
    """Test comparison operations."""
    assert safe_evaluate("5 > 3") is True
    assert safe_evaluate("5 < 3") is False
    assert safe_evaluate("5 == 5") is True
    assert safe_evaluate("5 != 3") is True
    assert safe_evaluate("5 >= 5") is True
    assert safe_evaluate("5 <= 3") is False


@pytest.mark.unit
def test_logical_operations():
    """Test logical operations."""
    assert safe_evaluate("True and True") is True
    assert safe_evaluate("True and False") is False
    assert safe_evaluate("True or False") is True
    assert safe_evaluate("not False") is True


@pytest.mark.unit
def test_safe_functions():
    """Test safe function calls."""
    assert safe_evaluate("abs(-5)") == 5
    assert safe_evaluate("round(3.7)") == 4
    assert safe_evaluate("min(1, 2, 3)") == 1
    assert safe_evaluate("max(1, 2, 3)") == 3
    assert safe_evaluate("sum([1, 2, 3])") == 6
    assert safe_evaluate("len('hello')") == 5


@pytest.mark.unit
def test_safe_constants():
    """Test safe constants."""
    evaluator = SafeEvaluator()
    assert evaluator.evaluate("pi") == pytest.approx(3.141592653589793)
    assert evaluator.evaluate("e") == pytest.approx(2.718281828459045)


@pytest.mark.unit
def test_context_variables():
    """Test evaluation with context variables."""
    context = {"x": 10, "y": 5}
    assert safe_evaluate("x + y", context=context) == 15
    assert safe_evaluate("x * y", context=context) == 50
    assert safe_evaluate("x > y", context=context) is True


@pytest.mark.unit
def test_complex_expressions():
    """Test complex expressions."""
    assert safe_evaluate("(2 + 3) * 4") == 20
    assert safe_evaluate("2 + 3 * 4") == 14
    assert safe_evaluate("abs(-10) + round(3.7)") == 14


@pytest.mark.unit
def test_security_unsafe_code():
    """Test that unsafe code is rejected."""
    # Should not allow __import__
    with pytest.raises(ValueError, match="Function '__import__' is not allowed"):
        safe_evaluate("__import__('os').system('ls')")

    # Should not allow eval
    with pytest.raises(ValueError, match="Function 'eval' is not allowed"):
        safe_evaluate("eval('1+1')")

    # Should not allow exec
    with pytest.raises(ValueError, match="Function 'exec' is not allowed"):
        safe_evaluate("exec('print(1)')")

    # Should not allow open
    with pytest.raises(ValueError, match="Function 'open' is not allowed"):
        safe_evaluate("open('/etc/passwd')")


@pytest.mark.unit
def test_security_unknown_variables():
    """Test that unknown variables raise errors."""
    with pytest.raises(ValueError, match="Unknown variable or constant"):
        safe_evaluate("unknown_var")


@pytest.mark.unit
def test_invalid_syntax():
    """Test that invalid syntax raises errors."""
    with pytest.raises(ValueError, match="Invalid expression syntax"):
        safe_evaluate("2 +")

    with pytest.raises(ValueError, match="Invalid expression syntax"):
        safe_evaluate("(")


@pytest.mark.unit
def test_empty_expression():
    """Test that empty expressions raise errors."""
    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        safe_evaluate("")

    with pytest.raises(ValueError, match="Expression must be a non-empty string"):
        safe_evaluate(None)


@pytest.mark.unit
def test_list_and_dict():
    """Test list and dictionary evaluation."""
    assert safe_evaluate("[1, 2, 3]") == [1, 2, 3]
    assert safe_evaluate("{'a': 1, 'b': 2}") == {"a": 1, "b": 2}
    assert safe_evaluate("(1, 2, 3)") == (1, 2, 3)


@pytest.mark.unit
def test_additional_functions():
    """Test adding custom safe functions."""
    custom_funcs = {"double": lambda x: x * 2}
    evaluator = SafeEvaluator(additional_functions=custom_funcs)
    assert evaluator.evaluate("double(5)") == 10
