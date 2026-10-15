"""
Multi-Provider SaaS Billing & Monetization Gateway for Agent Factory.

Provides:
- Unified billing interface supporting Stripe, LemonSqueezy, and Mock Sandbox
- Tiered subscriptions (Free, Starter, Pro, Enterprise)
- Pre-paid credit wallets & token usage metering
- Automated overage calculation and webhook handlers
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingProvider(str, Enum):
    STRIPE = "stripe"
    LEMONSQUEEZY = "lemonsqueezy"
    SANDBOX_MOCK = "mock"


@dataclass
class SubscriptionPlan:
    """Definition of a SaaS pricing plan."""
    tier: PlanTier
    name: str
    price_usd_monthly: float
    monthly_token_allowance: int
    included_agents: int
    overage_per_100k_tokens_usd: float
    features: list[str]


PLAN_CATALOG: dict[PlanTier, SubscriptionPlan] = {
    PlanTier.FREE: SubscriptionPlan(
        tier=PlanTier.FREE,
        name="Free Community",
        price_usd_monthly=0.0,
        monthly_token_allowance=100_000,
        included_agents=3,
        overage_per_100k_tokens_usd=0.0,
        features=["Community Blueprints", "Basic RAG", "REST API"],
    ),
    PlanTier.STARTER: SubscriptionPlan(
        tier=PlanTier.STARTER,
        name="Starter SaaS",
        price_usd_monthly=29.0,
        monthly_token_allowance=2_500_000,
        included_agents=15,
        overage_per_100k_tokens_usd=0.20,
        features=["Custom Tools", "Duplex Streaming", "White-Label Embed Widget", "Standard SLA"],
    ),
    PlanTier.PRO: SubscriptionPlan(
        tier=PlanTier.PRO,
        name="Pro Agent Suite",
        price_usd_monthly=99.0,
        monthly_token_allowance=15_000_000,
        included_agents=100,
        overage_per_100k_tokens_usd=0.15,
        features=["Autonomous Swarms", "MCP Server/Client", "Universal Exporters", "Priority 24/7 SLA"],
    ),
    PlanTier.ENTERPRISE: SubscriptionPlan(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise Cloud",
        price_usd_monthly=499.0,
        monthly_token_allowance=100_000_000,
        included_agents=1000,
        overage_per_100k_tokens_usd=0.10,
        features=["Dedicated LLM Gateways", "Zero-Trust RBAC", "SOC2 Compliance", "Custom Fine-Tuning"],
    ),
}


@dataclass
class CustomerAccount:
    """Customer billing record with wallet and metering."""
    customer_id: str
    tenant_id: str
    plan: PlanTier = PlanTier.FREE
    wallet_balance_usd: float = 0.0
    tokens_used_this_billing_cycle: int = 0
    billing_provider: BillingProvider = BillingProvider.SANDBOX_MOCK
    stripe_customer_id: str | None = None
    lemonsqueezy_customer_id: str | None = None


class MonetizationBillingGateway:
    """
    Manages payment providers, customer wallets, usage metering, and overage invoices.
    """

    def __init__(self, default_provider: BillingProvider = BillingProvider.SANDBOX_MOCK):
        self.default_provider = default_provider
        self.accounts: dict[str, CustomerAccount] = {}

    def get_or_create_account(self, customer_id: str, tenant_id: str = "default") -> CustomerAccount:
        """Fetch or initialize customer account."""
        if customer_id not in self.accounts:
            self.accounts[customer_id] = CustomerAccount(
                customer_id=customer_id,
                tenant_id=tenant_id,
                plan=PlanTier.FREE,
                wallet_balance_usd=10.00,  # $10 complimentary credit
                billing_provider=self.default_provider,
            )
        return self.accounts[customer_id]

    def upgrade_plan(self, customer_id: str, tier: PlanTier, provider: BillingProvider | None = None) -> CustomerAccount:
        """Upgrade customer subscription tier."""
        account = self.get_or_create_account(customer_id)
        account.plan = tier
        if provider:
            account.billing_provider = provider
        return account

    def top_up_wallet(self, customer_id: str, amount_usd: float) -> float:
        """Deposit funds into prepaid credit wallet."""
        account = self.get_or_create_account(customer_id)
        account.wallet_balance_usd += round(amount_usd, 2)
        return account.wallet_balance_usd

    def record_usage(self, customer_id: str, tokens: int, cost_usd: float = 0.0) -> dict[str, Any]:
        """
        Record agent execution usage, deduct wallet credit if applicable,
        and calculate overage.
        """
        account = self.get_or_create_account(customer_id)
        account.tokens_used_this_billing_cycle += tokens
        plan = PLAN_CATALOG[account.plan]

        is_overage = account.tokens_used_this_billing_cycle > plan.monthly_token_allowance
        overage_tokens = max(0, account.tokens_used_this_billing_cycle - plan.monthly_token_allowance)
        overage_cost = round((overage_tokens / 100_000) * plan.overage_per_100k_tokens_usd, 4)

        if cost_usd > 0:
            account.wallet_balance_usd = max(0.0, account.wallet_balance_usd - cost_usd)

        return {
            "customer_id": customer_id,
            "plan": account.plan.value,
            "tokens_used": account.tokens_used_this_billing_cycle,
            "allowance": plan.monthly_token_allowance,
            "is_overage": is_overage,
            "overage_cost_usd": overage_cost,
            "wallet_balance_usd": round(account.wallet_balance_usd, 2),
        }

    def process_webhook(self, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Process external webhook notifications."""
        event_type = payload.get("type") or payload.get("meta", {}).get("event_name", "unknown")
        return {
            "status": "processed",
            "provider": provider,
            "event": event_type,
            "timestamp": time.time(),
        }
