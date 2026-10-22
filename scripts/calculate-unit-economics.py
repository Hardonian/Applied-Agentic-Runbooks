#!/usr/bin/env python3
"""
Unit Economics Calculator
Calculates CAC, LTV, payback period, and gross margin
"""

from datetime import datetime
from pathlib import Path


def calculate_unit_economics():
    """Calculate unit economics based on inputs"""
    
    import os
    import sys
    
    print("💰 Agent Factory Unit Economics Calculator")
    print("=" * 50)
    print("Founder, CEO & Operator: Scott Hardie")
    print()
    
    # Check for non-interactive mode (CI/CD)
    skip_interactive = os.getenv("SKIP_INTERACTIVE", "").lower() in ("true", "1", "yes")
    is_tty = sys.stdin.isatty()
    
    if skip_interactive or not is_tty:
        # Non-interactive mode - use defaults/placeholders
        print("Running in non-interactive mode - using placeholder values")
        print()
        marketing_spend = float(os.getenv("MARKETING_SPEND", "0"))
        new_customers = int(os.getenv("NEW_CUSTOMERS", "0"))
        arpu = float(os.getenv("ARPU", "49"))
        customer_lifetime = float(os.getenv("CUSTOMER_LIFETIME", "12"))
        gross_margin_pct = float(os.getenv("GROSS_MARGIN_PCT", "80")) / 100
    else:
        # Interactive mode
        print("Enter your metrics (or press Enter for defaults/placeholders):")
        print()
        
        # Marketing spend
        marketing_spend = input("Total marketing spend (last 30 days): $") or "0"
        marketing_spend = float(marketing_spend)
        
        # New customers
        new_customers = input("New customers acquired (last 30 days): ") or "0"
        new_customers = int(new_customers)
        
        # ARPU (Average Revenue Per User)
        arpu = input("Average Revenue Per User (ARPU) per month: $") or "49"
        arpu = float(arpu)
        
        # Customer lifetime (months)
        customer_lifetime = input("Average customer lifetime (months): ") or "12"
        customer_lifetime = float(customer_lifetime)
        
        # Gross margin (%)
        gross_margin_pct = input("Gross margin percentage (%): ") or "80"
        gross_margin_pct = float(gross_margin_pct) / 100
    
    # Calculate metrics
    cac = marketing_spend / new_customers if new_customers > 0 else 0
    ltv = arpu * customer_lifetime
    gross_margin = gross_margin_pct
    mrr = arpu * new_customers if new_customers > 0 else 0
    payback_period = cac / (mrr * gross_margin) if (mrr * gross_margin) > 0 else 0
    
    # LTV:CAC ratio
    ltv_cac_ratio = ltv / cac if cac > 0 else 0
    
    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d")
    report = f"""# Unit Economics Analysis

**Date:** {timestamp}  
**Founder, CEO & Operator:** Scott Hardie  
**Status:** {'PRELIMINARY (No Real Data)' if new_customers == 0 else 'BASED ON ACTUAL DATA'}

---

## Inputs

- **Marketing Spend (30 days):** ${marketing_spend:,.2f}
- **New Customers (30 days):** {new_customers}
- **ARPU (Monthly):** ${arpu:,.2f}
- **Customer Lifetime:** {customer_lifetime} months
- **Gross Margin:** {gross_margin_pct*100:.1f}%

---

## Calculated Metrics

### Customer Acquisition Cost (CAC)
**Formula:** Marketing Spend / New Customers

**CAC:** ${cac:,.2f}

{'⚠️  No customers yet - CAC cannot be calculated' if new_customers == 0 else '✅ Calculated from actual data'}

---

### Lifetime Value (LTV)
**Formula:** ARPU × Customer Lifetime

**LTV:** ${ltv:,.2f}

**Breakdown:**
- ARPU: ${arpu:,.2f}/month
- Lifetime: {customer_lifetime} months
- Total: ${ltv:,.2f}

---

### LTV:CAC Ratio
**Formula:** LTV / CAC

**Ratio:** {ltv_cac_ratio:.2f}:1

**Interpretation:**
{'⚠️  Cannot calculate (no customers)' if new_customers == 0 else ('✅ Excellent (>3:1)' if ltv_cac_ratio >= 3 else ('✅ Good (2-3:1)' if ltv_cac_ratio >= 2 else '⚠️  Needs improvement (<2:1)'))}

**Target:** 3:1 or higher

---

### Payback Period
**Formula:** CAC / (MRR × Gross Margin)

**Payback Period:** {payback_period:.1f} months

**Breakdown:**
- CAC: ${cac:,.2f}
- MRR: ${mrr:,.2f}
- Gross Margin: {gross_margin_pct*100:.1f}%
- Monthly Profit: ${mrr * gross_margin:,.2f}
- Payback: {payback_period:.1f} months

**Target:** <12 months (ideally <6 months)

---

### Gross Margin
**Gross Margin:** {gross_margin_pct*100:.1f}%

**Interpretation:**
{'✅ Excellent (>80%)' if gross_margin_pct >= 0.8 else ('✅ Good (70-80%)' if gross_margin_pct >= 0.7 else ('⚠️  Acceptable (60-70%)' if gross_margin_pct >= 0.6 else '⚠️  Needs improvement (<60%)'))}

**Target:** >70% for SaaS

---

## Summary

| Metric | Value | Status |
|--------|-------|--------|
| **CAC** | ${cac:,.2f} | {'⚠️  No data' if new_customers == 0 else '✅'} |
| **LTV** | ${ltv:,.2f} | ✅ |
| **LTV:CAC** | {ltv_cac_ratio:.2f}:1 | {'⚠️  No data' if new_customers == 0 else ('✅' if ltv_cac_ratio >= 3 else '⚠️')} |
| **Payback** | {payback_period:.1f} months | {'⚠️  No data' if new_customers == 0 else ('✅' if payback_period < 12 else '⚠️')} |
| **Gross Margin** | {gross_margin_pct*100:.1f}% | {'✅' if gross_margin_pct >= 0.7 else '⚠️'} |

---

## Assumptions

**Current Assumptions:**
- ARPU: ${arpu:,.2f}/month (based on Starter tier pricing)
- Customer Lifetime: {customer_lifetime} months (typical SaaS churn)
- Gross Margin: {gross_margin_pct*100:.1f}% (infrastructure costs)

**Note:** {'These are placeholder calculations. Update with real data as you acquire customers.' if new_customers == 0 else 'Based on actual customer data.'}

---

## Next Steps

1. **Track Marketing Spend:**
   - Document all marketing channels
   - Track spend by channel
   - Measure signups by channel

2. **Calculate Channel-Specific CAC:**
   - CAC by channel (SEO, paid ads, referrals, etc.)
   - Identify most efficient channels
   - Double down on efficient channels

3. **Measure Customer Lifetime:**
   - Track churn rate
   - Calculate actual customer lifetime
   - Update LTV calculations

4. **Optimize Unit Economics:**
   - Reduce CAC (improve conversion, optimize channels)
   - Increase LTV (reduce churn, upsell, expand usage)
   - Improve gross margin (optimize infrastructure costs)

---

**Last Updated:** {timestamp}  
**Next Review:** [Set monthly review]

---

## How to Use This

**For YC Application:**
- Include CAC, LTV, payback period
- Show LTV:CAC ratio (target: >3:1)
- Explain assumptions

**For Investor Meetings:**
- Show unit economics trend (improving over time)
- Compare to industry benchmarks
- Explain path to profitability

**For Internal Planning:**
- Use to set marketing budgets
- Calculate payback period
- Plan for profitability

"""

    # Save report
    output_file = Path("yc/UNIT_ECONOMICS.md")
    output_file.write_text(report)
    
    print()
    print("✅ Unit economics calculated!")
    print(f"📄 Report saved to: {output_file}")
    print()
    print("Summary:")
    print(f"  CAC: ${cac:,.2f}")
    print(f"  LTV: ${ltv:,.2f}")
    print(f"  LTV:CAC: {ltv_cac_ratio:.2f}:1")
    print(f"  Payback: {payback_period:.1f} months")
    print()
    print("Next steps:")
    print("  1. Review report: cat yc/UNIT_ECONOMICS.md")
    print("  2. Update with real data as you acquire customers")
    print("  3. Track metrics monthly")

if __name__ == "__main__":
    calculate_unit_economics()
