"""Tests for AgentComplianceCertification generator."""

import pytest

from agent_factory.agents.agent import Agent, AgentConfig
from agent_factory.compliance.certification import (
    AgentCertificationGenerator,
    CertificationGrade,
    RiskTier,
)
from agent_factory.core.guardrails import Guardrails, SQLInjectionGuardrail


@pytest.mark.unit
def test_agent_certification_generation():
    """Verify compliance certificate generation with guardrails and boundaries."""
    guardrails = Guardrails()
    guardrails.add_input_guardrail(SQLInjectionGuardrail())

    agent = Agent(
        id="certified-agent-1",
        name="Production Enterprise Agent",
        instructions="Provide verified business analysis.",
        model="gpt-4o",
        guardrails=guardrails,
        config=AgentConfig(max_tokens=4096, timeout=30),
    )

    cert = AgentCertificationGenerator.generate_certificate(agent)

    assert cert.certificate_id.startswith("AF-CERT-")
    assert cert.agent_id == "certified-agent-1"
    assert cert.grade in [CertificationGrade.GRADE_A_PLUS, CertificationGrade.GRADE_A]
    assert cert.overall_score >= 90
    assert cert.risk_tier == RiskTier.MINIMAL_RISK
    assert len(cert.integrity_hash) == 64
    assert len(cert.digital_seal) == 64
    assert cert.controls_evaluated > 0

    # Verify JSON export
    data = cert.to_dict()
    assert data["certificate_id"] == cert.certificate_id
    assert data["grade"] in ["A+", "A"]
    assert "evidence_trail" in data

    # Verify Markdown export
    md = cert.to_markdown()
    assert "# 🛡️ Agent Factory Production Certification Record" in md
    assert "certified-agent-1" in md
    assert "OWASP LLM Top 10 Score" in md


@pytest.mark.unit
def test_agent_integrity_hash_changes_with_instructions():
    """Verify cryptographic fingerprint detects any modification to agent instructions."""
    agent1 = Agent(
        id="agent-hash-test",
        name="Agent 1",
        instructions="Original instructions.",
        model="gpt-4o",
    )
    hash1 = AgentCertificationGenerator.compute_integrity_hash(agent1)

    agent2 = Agent(
        id="agent-hash-test",
        name="Agent 1",
        instructions="Modified malicious prompt injection instructions.",
        model="gpt-4o",
    )
    hash2 = AgentCertificationGenerator.compute_integrity_hash(agent2)

    assert hash1 != hash2
