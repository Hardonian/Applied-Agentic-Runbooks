# Metrics Snapshot

**Date:** 2026-10-01  
**Founder, CEO & Operator:** Scott Hardie  
**Source:** Production deployment at http://localhost:8000

---

## Current Metrics (Baseline)

### Users
- **Total Signups:** [TO BE FILLED - check database or admin panel]
- **Active Users (DAU):** [TO BE FILLED]
- **Activated Users:** [TO BE FILLED] (deployed first agent)
- **Retention:**
  - Day 1: [TO BE FILLED]%
  - Day 7: [TO BE FILLED]%
  - Day 30: [TO BE FILLED]%

**How to Get:**
```sql
-- Query database for user counts
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(*) as activated_users FROM users WHERE activated_at IS NOT NULL;
```

### Usage
- **Agent Runs:** [TO BE FILLED - check telemetry events]
- **API Calls:** [TO BE FILLED]
- **Workflows Executed:** [TO BE FILLED]
- **Blueprints Installed:** [TO BE FILLED]

**How to Get:**
```sql
-- Query telemetry events
SELECT COUNT(*) as agent_runs FROM events WHERE event_type = 'AGENT_RUN';
SELECT COUNT(*) as blueprint_installs FROM events WHERE event_type = 'BLUEPRINT_INSTALL';
```

Or check metrics endpoint: `curl http://localhost:8000/metrics`

### Revenue
- **MRR:** $0 (pre-revenue)
- **ARR:** $0
- **Customers:** 0 (paying)
- **ARPU:** [TO BE FILLED]

**Status:** Pre-revenue - need first paying customers

### Growth
- **MoM Growth Rate:** [TO BE FILLED]%
- **Signup Rate:** [TO BE FILLED] signups/week
- **Activation Rate:** [TO BE FILLED]% (signup → activation)

---

## Metrics Collection Commands

### Check Health
```bash
curl http://localhost:8000/health
```

### Get Metrics (Prometheus format)
```bash
curl http://localhost:8000/metrics
```

### Query Database Directly
```bash
# Connect to Supabase/PostgreSQL
psql $DATABASE_URL

# Count users
SELECT COUNT(*) FROM users;

# Count agent runs
SELECT COUNT(*) FROM events WHERE event_type = 'AGENT_RUN';

# Count by date
SELECT DATE(created_at), COUNT(*) 
FROM events 
WHERE event_type = 'AGENT_RUN' 
GROUP BY DATE(created_at) 
ORDER BY DATE(created_at) DESC;
```

---

## Metrics Infrastructure Status

**Telemetry:** ✅ Ready (agent_factory/telemetry/)  
**Metrics Endpoint:** ✅ Ready (http://localhost:8000/metrics)  
**Health Check:** ✅ Ready (http://localhost:8000/health)  
**Dashboard:** ⚠️ Not deployed (infrastructure ready)

**Events Tracked:**
- `USER_SIGNUP`, `USER_LOGIN`, `USER_ACTIVATED`
- `AGENT_RUN`, `WORKFLOW_RUN`
- `BLUEPRINT_INSTALL`
- `BILLING_USAGE`, `REVENUE`
- `REFERRAL_SENT`, `REFERRAL_CONVERTED`

---

## Next Steps

1. **Use the app yourself:**
   - Create agents
   - Run agents
   - Install blueprints
   - Generate activity

2. **Query metrics:**
   - Use commands above
   - Check database directly
   - Use metrics endpoint

3. **Set up dashboard:**
   - Mixpanel (recommended for quick setup)
   - Amplitude
   - Grafana + Prometheus

4. **Document baseline:**
   - Fill in numbers above (even if zeros)
   - Update this file weekly
   - Track progress

---

**Last Updated:** 2026-10-01  
**Next Update:** [Set weekly reminder]

