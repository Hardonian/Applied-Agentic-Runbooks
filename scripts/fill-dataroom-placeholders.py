#!/usr/bin/env python3
"""
Fill Data Room Placeholders
Helps identify and fill [TO BE FILLED] sections in data room docs
"""

import re
from datetime import datetime
from pathlib import Path


def find_placeholders():
    """Find all [TO BE FILLED] placeholders in data room"""
    
    dataroom_dir = Path("dataroom")
    placeholders = []
    
    for file in dataroom_dir.glob("*.md"):
        content = file.read_text()
        matches = re.findall(r'\[TO BE FILLED[^\]]*\]|\[TBD\]|\[DATE\]|\[NUMBER\]|\[AMOUNT\]', content, re.IGNORECASE)
        
        if matches:
            placeholders.append({
                'file': str(file),
                'count': len(matches),
                'examples': matches[:5]
            })
    
    return placeholders

def generate_fill_guide():
    """Generate guide for filling placeholders"""
    
    placeholders = find_placeholders()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    
    guide = f"""# Data Room Placeholder Fill Guide

**Founder, CEO & Operator:** Scott Hardie  
**Generated:** {timestamp}

---

## Placeholders Found

"""
    
    total = 0
    for item in placeholders:
        guide += f"### {Path(item['file']).name}\n"
        guide += f"- **File:** `{item['file']}`\n"
        guide += f"- **Placeholders:** {item['count']}\n"
        guide += f"- **Examples:** {', '.join(item['examples'][:3])}\n"
        guide += "\n"
        total += item['count']
    
    guide += f"""
**Total Placeholders:** {total}

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
- Current date: {timestamp}
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

**Last Updated:** {timestamp}
"""
    
    output_file = Path("docs/DATAROOM_FILL_GUIDE.md")
    output_file.write_text(guide)
    
    print("📋 Data Room Placeholder Analysis")
    print("=" * 50)
    print(f"Found {len(placeholders)} files with placeholders")
    print(f"Total placeholders: {total}")
    print()
    print("Files with placeholders:")
    for item in placeholders:
        print(f"  - {Path(item['file']).name}: {item['count']} placeholders")
    print()
    print(f"✅ Fill guide created: {output_file}")
    print()
    print("Next steps:")
    print("  1. Review guide: cat docs/DATAROOM_FILL_GUIDE.md")
    print("  2. Run scripts to collect data")
    print("  3. Fill placeholders systematically")

if __name__ == "__main__":
    find_placeholders()
    generate_fill_guide()
