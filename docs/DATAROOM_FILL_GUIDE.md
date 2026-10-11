# Data Room Placeholder Fill Guide

**Founder, CEO & Operator:** Scott Hardie  
**Generated:** 2026-10-01

---

## Placeholders Found

### 02_PRODUCT_DECK_OUTLINE.md
- **File:** `dataroom/02_PRODUCT_DECK_OUTLINE.md`
- **Placeholders:** 10
- **Examples:** [Date], [TO BE FILLED], [TBD]

### APPLICATION_ANSWERS_YC_DRAFT.md
- **File:** `dataroom/APPLICATION_ANSWERS_YC_DRAFT.md`
- **Placeholders:** 11
- **Examples:** [TO BE FILLED - e.g., agentfactory.io], [TO BE FILLED - production URL or demo video], [TO BE FILLED]

### 01_EXEC_SUMMARY.md
- **File:** `dataroom/01_EXEC_SUMMARY.md`
- **Placeholders:** 10
- **Examples:** [TO BE FILLED - See `yc/METRICS_SNAPSHOT.md`], [TBD], [TBD]

### 07_CAP_TABLE_PLACEHOLDER.md
- **File:** `dataroom/07_CAP_TABLE_PLACEHOLDER.md`
- **Placeholders:** 8
- **Examples:** [TO BE FILLED BY FOUNDERS], [TO BE FILLED], [TO BE FILLED]

### 04_CUSTOMER_PROOF.md
- **File:** `dataroom/04_CUSTOMER_PROOF.md`
- **Placeholders:** 5
- **Examples:** [TO BE FILLED], [TO BE FILLED], [TO BE FILLED]

### 03_METRICS_OVERVIEW.md
- **File:** `dataroom/03_METRICS_OVERVIEW.md`
- **Placeholders:** 23
- **Examples:** [TO BE FILLED], [TBD], [TBD]


**Total Placeholders:** 67

---

## How to Fill

### 1. Metrics Placeholders

**Files:** `dataroom/03_METRICS_OVERVIEW.md`, `dataroom/01_EXEC_SUMMARY.md`

**Fill With:**
- Real numbers from `yc/METRICS_SNAPSHOT.md`
- Or document baseline (even if zeros)
- Use format: "0 (pre-revenue)" or "[NUMBER]"

**Commands:**
\`\`\`bash
make metrics-collect
# Then fill in numbers from yc/METRICS_SNAPSHOT.md
\`\`\`

---

### 2. Customer Placeholders

**Files:** `dataroom/04_CUSTOMER_PROOF.md`

**Fill With:**
- Real customer names/quotes from `yc/CUSTOMER_TESTIMONIALS.md`
- Early adopter info from `yc/EARLY_ADOPTERS.md`
- Case studies from `yc/CASE_STUDIES.md`

**Commands:**
\`\`\`bash
bash scripts/get-users-checklist.sh
# Then fill in customer info
\`\`\`

---

### 3. Unit Economics Placeholders

**Files:** `dataroom/01_EXEC_SUMMARY.md`, `dataroom/03_METRICS_OVERVIEW.md`

**Fill With:**
- Calculations from `yc/UNIT_ECONOMICS.md`

**Commands:**
\`\`\`bash
make unit-economics
# Then fill in CAC, LTV, payback period
\`\`\`

---

### 4. Date Placeholders

**Files:** All data room files

**Fill With:**
- Current date: 2026-10-01
- Or specific dates (e.g., submission date)

---

### 5. URL Placeholders

**Files:** `dataroom/01_EXEC_SUMMARY.md`, `dataroom/APPLICATION_ANSWERS_YC_DRAFT.md`

**Fill With:**
- Production URL: https://your-domain.com
- Demo video URL: [YouTube/Vimeo link]

---

## Quick Fill Checklist

- [ ] Run: `make metrics-collect` → Fill metrics placeholders
- [ ] Run: `make unit-economics` → Fill unit economics placeholders
- [ ] Get users → Fill customer placeholders
- [ ] Deploy production → Fill URL placeholders
- [ ] Set dates → Fill date placeholders

---

## Search & Replace Guide

**Find all placeholders:**
\`\`\`bash
grep -r "TO BE FILLED\|TBD\|\[DATE\]\|\[NUMBER\]\|\[AMOUNT\]" dataroom/
\`\`\`

**Fill systematically:**
1. Metrics first (easiest - use scripts)
2. Customers second (need real users)
3. URLs third (need production)
4. Dates last (quick)

---

**Last Updated:** 2026-10-01
