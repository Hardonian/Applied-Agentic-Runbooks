"""
Zero-Trust Capability Tokens for Tool Execution in Agent Factory.

Ensures tools (e.g. database execution, file write, shell commands) can only
be invoked with valid, time-bounded HMAC-SHA256 capability tokens granted to the agent.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


class CapabilityTokenManager:
    """
    Issues and verifies time-bounded cryptographic capability tokens for tool execution.
    """

    def __init__(self, secret_key: str | None = None):
        # No default secret. A hardcoded fallback here would be a public,
        # forgeable HMAC key: anyone who can read this file could mint
        # capability tokens for tool execution (database exec, file write,
        # shell). The key must be supplied explicitly -- or via the
        # AGENT_FACTORY_CAPABILITY_SECRET environment variable, which is the
        # documented deployment path.
        if secret_key is None:
            secret_key = os.environ.get("AGENT_FACTORY_CAPABILITY_SECRET", "")
        if not secret_key:
            raise ValueError(
                "CapabilityTokenManager requires an explicit secret_key "
                "(or the AGENT_FACTORY_CAPABILITY_SECRET environment variable); "
                "refusing to default to a public value."
            )
        self.secret_key = secret_key.encode("utf-8")

    def issue_token(
        self,
        agent_id: str,
        tool_name: str,
        expires_in_seconds: int = 300,
        allowed_params: dict[str, Any] | None = None,
    ) -> str:
        """
        Issue a signed capability token for a specific agent and tool.
        """
        payload = {
            "agent_id": agent_id,
            "tool_name": tool_name,
            "exp": time.time() + expires_in_seconds,
            "allowed_params": allowed_params or {},
        }
        raw_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(self.secret_key, raw_json.encode("utf-8"), hashlib.sha256).hexdigest()
        
        token_data = {
            "payload": payload,
            "signature": signature,
        }
        return base64.urlsafe_b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")

    def verify_token(self, token: str, agent_id: str, tool_name: str) -> bool:
        """
        Verify that a capability token is authentic, unexpired, and granted for the target tool.
        """
        try:
            raw_bytes = base64.urlsafe_b64decode(token.encode("utf-8"))
            token_data = json.loads(raw_bytes.decode("utf-8"))

            payload = token_data.get("payload", {})
            signature = token_data.get("signature", "")

            # Check expiration
            if time.time() > payload.get("exp", 0):
                return False

            # Check target match
            if payload.get("agent_id") != agent_id or payload.get("tool_name") != tool_name:
                return False

            # Verify cryptographic signature
            raw_json = json.dumps(payload, sort_keys=True)
            expected_sig = hmac.new(self.secret_key, raw_json.encode("utf-8"), hashlib.sha256).hexdigest()

            return hmac.compare_digest(signature, expected_sig)
        except Exception:
            return False
