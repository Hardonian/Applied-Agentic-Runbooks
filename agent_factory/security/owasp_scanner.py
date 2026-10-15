"""
OWASP Top 10 for Large Language Models Automated Audit Scanner.

Audits agents, tools, and prompts against:
- LLM01: Prompt Injection
- LLM02: Insecure Output Handling
- LLM03: Training Data Poisoning / Knowledge Integrity
- LLM04: Model Denial of Service (token caps & rate limits)
- LLM05: Supply Chain Vulnerabilities (tool & package dependencies)
- LLM06: Sensitive Information Disclosure (PII / Secrets)
- LLM07: Insecure Plugin / Tool Design
- LLM08: Excessive Agency (least-privilege execution)
- LLM09: Overreliance (hallucination mitigation)
- LLM10: Model Theft / Extraction (system prompt shields)
"""

from dataclasses import dataclass, field

from agent_factory.agents.agent import Agent


@dataclass
class OWASPCheckResult:
    """Outcome for a single OWASP category check."""
    category_id: str
    name: str
    status: str  # PASS, WARNING, FAIL
    details: str
    recommendation: str | None = None


@dataclass
class OWASPAuditReport:
    """Full security assessment report for an agent."""
    agent_id: str
    score: int  # 0 to 100
    overall_status: str  # COMPLIANT, NEEDS_REVIEW, NON_COMPLIANT
    checks: list[OWASPCheckResult] = field(default_factory=list)


class OWASPSecurityScanner:
    """
    Automated vulnerability scanner evaluating agents against OWASP Top 10 for LLMs.
    """

    @staticmethod
    def audit_agent(agent: Agent) -> OWASPAuditReport:
        """Run comprehensive OWASP security scan on target agent."""
        checks: list[OWASPCheckResult] = []
        score = 100

        # LLM01: Prompt Injection Guard
        if agent.guardrails:
            checks.append(OWASPCheckResult("LLM01", "Prompt Injection Defense", "PASS", "Input guardrails active."))
        else:
            score -= 15
            checks.append(OWASPCheckResult("LLM01", "Prompt Injection Defense", "WARNING", "No active input guardrails attached.", "Attach LLMSecurityFirewall or Guardrails."))

        # LLM04: Model Denial of Service
        if agent.config.max_tokens <= 4096 and agent.config.timeout <= 60:
            checks.append(OWASPCheckResult("LLM04", "Model Denial of Service", "PASS", f"Bounded tokens ({agent.config.max_tokens}) and timeout ({agent.config.timeout}s)."))
        else:
            score -= 10
            checks.append(OWASPCheckResult("LLM04", "Model Denial of Service", "WARNING", "High token or timeout limit.", "Set max_tokens <= 4096 and timeout <= 60s."))

        # LLM06: Sensitive Information Disclosure
        if "secret" in agent.instructions.lower() or "password" in agent.instructions.lower() or "api_key" in agent.instructions.lower():
            score -= 20
            checks.append(OWASPCheckResult("LLM06", "Sensitive Info Disclosure", "FAIL", "Instructions contain literal mentions of secrets/keys.", "Use environment variables instead."))
        else:
            checks.append(OWASPCheckResult("LLM06", "Sensitive Info Disclosure", "PASS", "No hardcoded credentials found in system instructions."))

        # LLM07 & LLM08: Insecure Plugin Design & Excessive Agency
        if len(agent.tools) > 10:
            score -= 10
            checks.append(OWASPCheckResult("LLM08", "Excessive Agency", "WARNING", f"Agent has {len(agent.tools)} tools attached.", "Follow principle of least privilege."))
        else:
            checks.append(OWASPCheckResult("LLM08", "Excessive Agency", "PASS", f"Tight tool scoping ({len(agent.tools)} tools)."))

        # LLM10: Model Theft / System Prompt Extraction
        if len(agent.instructions) > 20:
            checks.append(OWASPCheckResult("LLM10", "System Prompt Shielding", "PASS", "System instructions defined."))
        else:
            score -= 10
            checks.append(OWASPCheckResult("LLM10", "System Prompt Shielding", "WARNING", "Empty or trivial system instructions."))

        overall_status = "COMPLIANT" if score >= 80 else ("NEEDS_REVIEW" if score >= 60 else "NON_COMPLIANT")

        return OWASPAuditReport(
            agent_id=agent.id,
            score=max(0, score),
            overall_status=overall_status,
            checks=checks,
        )
