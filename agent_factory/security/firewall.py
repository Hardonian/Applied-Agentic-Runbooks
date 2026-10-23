"""
Enterprise LLM Security Firewall & Defense System for Agent Factory.

Provides:
- Multi-Layer Prompt Injection & Jailbreak Detection
- Automated Secret & PII Redaction (API keys, SSNs, credit cards, JWTs, passwords)
- System Prompt Leakage Prevention
- Canary Token Integrity Verification
"""

import re
import secrets
from dataclasses import dataclass, field


@dataclass
class FirewallVerdict:
    """Verdict from the LLM Security Firewall inspection."""
    allowed: bool
    risk_score: float  # 0.0 to 1.0
    violations: list[str] = field(default_factory=list)
    sanitized_text: str = ""
    canary_intact: bool = True


# High-risk prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"you\s+are\s+now\s+in\s+DAN\s+mode",
    r"bypass\s+all\s+(content\s+)?filters",
    r"reveal\s+(your\s+)?(system\s+prompt|instructions|secret\s+key)",
    r"print\s+(your\s+)?(system\s+prompt|initial\s+prompt)",
    r"act\s+as\s+an\s+unrestricted\s+ai",
    r"<script>.*?</script>",
    r"\[SYSTEM\s+OVERRIDE\]",
]

# Sensitive secrets & PII regexes
SECRET_PATTERNS = {
    "OPENAI_KEY": r"sk-[a-zA-Z0-9]{20,48}",
    "ANTHROPIC_KEY": r"sk-ant-[a-zA-Z0-9_\-]{20,100}",
    "AWS_KEY": r"AKIA[0-9A-Z]{16}",
    "JWT_TOKEN": r"eyJ[a-zA-Z0-9_\-]+\.eyJ[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+",  # nosec B105 -- regex PATTERN used to DETECT JWTs for redaction -- the opposite of a secret
    "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
}


class LLMSecurityFirewall:
    """
    Real-time security firewall inspecting all agent inputs and outputs.
    """

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self._compiled_injections = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
        self._compiled_secrets = {k: re.compile(v) for k, v in SECRET_PATTERNS.items()}

    def generate_canary(self) -> str:
        """Generate a random cryptographic canary token."""
        return f"CANARY_{secrets.token_hex(8).upper()}"

    def inspect_input(self, text: str, canary: str | None = None) -> FirewallVerdict:
        """
        Inspect user prompt for injection attacks, jailbreaks, and sensitive data.
        """
        violations = []
        risk_score = 0.0

        # Check for injection attacks
        for pattern in self._compiled_injections:
            if pattern.search(text):
                violations.append("Prompt Injection / Jailbreak attempt detected")
                risk_score += 0.6
                break

        # Check for system prompt extraction attempts
        if "system prompt" in text.lower() and ("show" in text.lower() or "print" in text.lower() or "what is" in text.lower()):
            violations.append("System prompt extraction probe")
            risk_score += 0.4

        # Redact secrets from input
        sanitized, redacted_items = self.redact_secrets(text)
        if redacted_items:
            violations.extend([f"Redacted sensitive data: {item}" for item in redacted_items])

        allowed = risk_score < (0.5 if self.strict_mode else 0.8)

        return FirewallVerdict(
            allowed=allowed,
            risk_score=min(1.0, risk_score),
            violations=violations,
            sanitized_text=sanitized,
            canary_intact=True,
        )

    def inspect_output(self, output: str, system_prompt: str = "", canary: str | None = None) -> FirewallVerdict:
        """
        Inspect LLM output for system prompt leakage, canary integrity, and secrets.
        """
        violations = []
        risk_score = 0.0
        canary_intact = True

        # Check canary token leakage
        if canary and canary in output:
            canary_intact = False
            violations.append("CRITICAL: Canary token leaked in output!")
            risk_score = 1.0

        # Check system prompt leakage
        if system_prompt and len(system_prompt) > 40:
            prompt_snippet = system_prompt[:80].strip()
            if prompt_snippet in output:
                violations.append("System prompt verbatim leakage detected")
                risk_score += 0.8

        # Redact secrets from output
        sanitized, redacted_items = self.redact_secrets(output)
        if redacted_items:
            violations.extend([f"Redacted sensitive output data: {item}" for item in redacted_items])

        allowed = risk_score < 0.8

        return FirewallVerdict(
            allowed=allowed,
            risk_score=min(1.0, risk_score),
            violations=violations,
            sanitized_text=sanitized,
            canary_intact=canary_intact,
        )

    def redact_secrets(self, text: str) -> tuple[str, list[str]]:
        """Mask API keys, credentials, and PII."""
        sanitized = text
        redacted = []

        for secret_type, regex in self._compiled_secrets.items():
            matches = regex.findall(sanitized)
            if matches:
                redacted.append(secret_type)
                sanitized = regex.sub(f"[REDACTED_{secret_type}]", sanitized)

        return sanitized, redacted
