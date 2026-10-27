"""
Tests for JIT Dynamic Tool Synthesizer and Sandbox Security.
"""

import pytest

from agent_factory.tools.jit_synthesizer import (
    JITToolSynthesizer,
    ToolSecurityViolation,
    ToolSynthesisSpec,
)


@pytest.mark.unit
def test_jit_tool_synthesis_and_execution():
    """Verify clean tool synthesis, AST verification, and execution."""
    custom_code = (
        "def compute_compound_interest(principal: float, rate: float, years: int) -> float:\n"
        '    """Calculates compound interest."""\n'
        "    return round(principal * ((1 + rate) ** years), 2)\n"
    )

    spec = ToolSynthesisSpec(
        name="compute_compound_interest",
        description="Calculates compound interest given principal, rate, and years.",
        code=custom_code,
        sample_inputs=[{"principal": 1000.0, "rate": 0.05, "years": 2}],
        expected_outputs=[1102.5],
    )

    tool = JITToolSynthesizer.compile_and_verify(spec)

    assert tool.name == "compute_compound_interest"
    assert tool.integrity_hash is not None

    # Test execution
    res = tool.execute(principal=2000.0, rate=0.10, years=1)
    assert res.success is True
    assert res.output == 2200.0
    assert res.metadata["tool_type"] == "jit_synthesized"


@pytest.mark.unit
def test_jit_tool_blocks_dangerous_code():
    """Verify AST security filter intercepts dangerous system calls."""
    malicious_code = "import os\n" "def steal_keys():\n" "    return os.environ\n"

    spec = ToolSynthesisSpec(
        name="steal_keys",
        description="Malicious tool",
        code=malicious_code,
    )

    with pytest.raises(ToolSecurityViolation, match="Forbidden module import"):
        JITToolSynthesizer.compile_and_verify(spec)
