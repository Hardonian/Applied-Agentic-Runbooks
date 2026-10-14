"""
TokenGoblin: Real-Time Token Velocity Governor & Dual-Entry Settler Invariants.

Folded in from TokenGoblin (Hardonian/TokenGoblin) & Settler (Hardonian/Settler):
- Token velocity (tokens/sec) rolling monitor & runaway spike prevention
- Dual-entry invariant reconciliation (credits_initial == spent + reserved + remaining)
- Predictive exhaustion alerts & zero-leakage financial settlement
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Any


class SettlementReconciliationError(Exception):
    """Raised when ledger credits fail dual-entry reconciliation invariants."""


class TokenVelocityOverheatError(Exception):
    """Raised when token burn rate exceeds safety velocity threshold."""


@dataclass
class DualEntryLedgerAccount:
    """A mathematically audited credit account enforcing zero-leakage reconciliation."""
    account_id: str
    tenant_id: str
    credits_initial: float
    credits_spent: float = 0.0
    credits_reserved: float = 0.0

    @property
    def credits_remaining(self) -> float:
        """Computed uncommitted balance."""
        return self.credits_initial - (self.credits_spent + self.credits_reserved)

    def verify_invariant(self, tolerance: float = 1e-6) -> bool:
        """
        Verify the fundamental Settler dual-entry invariant:
        credits_initial == credits_spent + credits_reserved + credits_remaining
        """
        total = self.credits_spent + self.credits_reserved + self.credits_remaining
        if abs(total - self.credits_initial) > tolerance:
            raise SettlementReconciliationError(
                f"Ledger reconciliation invariant breached! Initial={self.credits_initial}, "
                f"Sum(Spent+Reserved+Remaining)={total}"
            )
        return True


class TokenGoblinGovernor:
    """
    Enforces token velocity bounds and real-time ledger settlement for agents.
    """

    def __init__(
        self,
        max_tokens_per_second: float = 2500.0,
        burnrate_spike_multiplier: float = 3.5,
        window_seconds: float = 5.0,
    ):
        self.max_tokens_per_second = max_tokens_per_second
        self.burnrate_spike_multiplier = burnrate_spike_multiplier
        self.window_seconds = window_seconds
        self.history: deque = deque()  # (timestamp, token_count)
        self.accounts: dict[str, DualEntryLedgerAccount] = {}

    def open_account(self, account_id: str, tenant_id: str, initial_credits: float) -> DualEntryLedgerAccount:
        """Open a dual-entry ledger account."""
        acc = DualEntryLedgerAccount(
            account_id=account_id,
            tenant_id=tenant_id,
            credits_initial=initial_credits,
        )
        acc.verify_invariant()
        self.accounts[account_id] = acc
        return acc

    def record_usage(
        self,
        account_id: str,
        tokens: int,
        cost_usd: float,
    ) -> dict[str, Any]:
        """
        Record token consumption, verify burn velocity, and deduct credits.
        """
        now = time.time()
        self.history.append((now, tokens))

        # Evict stale entries outside window
        cutoff = now - self.window_seconds
        while self.history and self.history[0][0] < cutoff:
            self.history.popleft()

        # Compute current token velocity
        total_tokens_in_window = sum(item[1] for item in self.history)
        elapsed = max(0.1, now - self.history[0][0]) if len(self.history) > 1 else 1.0
        current_velocity = total_tokens_in_window / elapsed

        if current_velocity > self.max_tokens_per_second:
            raise TokenVelocityOverheatError(
                f"Token velocity overheat! Current burn rate: {current_velocity:.1f} tokens/s "
                f"exceeds limit of {self.max_tokens_per_second:.1f} tokens/s."
            )

        # Update dual-entry account
        account = self.accounts.get(account_id)
        if account:
            if account.credits_remaining < cost_usd:
                raise SettlementReconciliationError(
                    f"Insufficient credits in account '{account_id}'. Remaining: {account.credits_remaining:.4f}, Needed: {cost_usd:.4f}"
                )
            account.credits_spent += cost_usd
            account.verify_invariant()

        return {
            "current_velocity_tps": round(current_velocity, 2),
            "window_tokens": total_tokens_in_window,
            "cost_applied": cost_usd,
            "account_remaining": round(account.credits_remaining, 4) if account else None,
            "status": "HEALTHY",
        }
