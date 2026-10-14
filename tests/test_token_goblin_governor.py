"""
Tests for TokenGoblin velocity governor and Settler dual-entry ledger.
"""

import pytest

from agent_factory.financial.token_goblin import (
    DualEntryLedgerAccount,
    TokenGoblinGovernor,
    TokenVelocityOverheatError,
)


@pytest.mark.unit
def test_dual_entry_ledger_invariants():
    """Verify Settler dual-entry mathematical invariants."""
    account = DualEntryLedgerAccount(
        account_id="acc-001",
        tenant_id="tenant-corp",
        credits_initial=100.0,
    )
    assert account.credits_remaining == 100.0
    assert account.verify_invariant() is True

    # Spend 25.0
    account.credits_spent = 25.0
    assert account.credits_remaining == 75.0
    assert account.verify_invariant() is True

    # Reserve 20.0
    account.credits_reserved = 20.0
    assert account.credits_remaining == 55.0
    assert account.verify_invariant() is True


@pytest.mark.unit
def test_token_goblin_velocity_and_deduction():
    """Verify governor tracks burnrate and deducts from dual-entry balance."""
    governor = TokenGoblinGovernor(max_tokens_per_second=5000.0)
    governor.open_account("acc-test", "tenant-1", initial_credits=10.0)

    # Normal usage
    rec = governor.record_usage("acc-test", tokens=500, cost_usd=0.05)
    assert rec["status"] == "HEALTHY"
    assert rec["account_remaining"] == 9.95

    # Overheat trigger with ultra-low limit
    strict_gov = TokenGoblinGovernor(max_tokens_per_second=100.0)
    with pytest.raises(TokenVelocityOverheatError, match="Token velocity overheat"):
        strict_gov.record_usage("acc-test", tokens=1000, cost_usd=0.01)
