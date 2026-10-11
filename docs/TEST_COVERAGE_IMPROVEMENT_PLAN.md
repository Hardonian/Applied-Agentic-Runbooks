# Test Coverage Improvement Plan

**Founder, CEO & Operator:** Scott Hardie  
**Current Coverage:** 0%  
**Target Coverage:** 80%+  
**Last Updated:** 2026-10-01

---

## Current Status

**Coverage:** 0%  
**Target:** 80%+  
**Gap:** 80% to reach target

---

## Priority Areas (By Impact)

### 1. API Endpoints (HIGH PRIORITY)

**Current:** Partial coverage  
**Target:** 80%+ coverage

**Files to Test:**
- `agent_factory/api/routes/agents.py`
- `agent_factory/api/routes/workflows.py`
- `agent_factory/api/routes/blueprints.py`
- `agent_factory/api/routes/auth.py`

**Test Cases Needed:**
- [ ] Create agent (success)
- [ ] Create agent (validation errors)
- [ ] Run agent (success)
- [ ] Run agent (errors)
- [ ] List agents
- [ ] Update agent
- [ ] Delete agent
- [ ] Authentication required
- [ ] Authorization checks

**Estimated Effort:** 2-3 days

---

### 2. Core Agent Functionality (HIGH PRIORITY)

**Current:** ✅ Good coverage  
**Target:** Maintain 80%+

**Files:**
- `agent_factory/core/agent.py`
- `agent_factory/core/tool.py`

**Test Cases Needed:**
- [ ] Agent creation
- [ ] Agent execution
- [ ] Tool integration
- [ ] Error handling
- [ ] Retry logic

**Estimated Effort:** 1-2 days

---

### 3. Workflow Orchestration (MEDIUM PRIORITY)

**Current:** Partial coverage  
**Target:** 80%+ coverage

**Files:**
- `agent_factory/workflows/model.py`
- `agent_factory/workflows/executor.py`

**Test Cases Needed:**
- [ ] Workflow creation
- [ ] Workflow execution
- [ ] Agent chaining
- [ ] Error handling
- [ ] Parallel execution

**Estimated Effort:** 2-3 days

---

### 4. Billing Integration (MEDIUM PRIORITY)

**Current:** ⚠️ Limited coverage  
**Target:** 80%+ coverage

**Files:**
- `agent_factory/billing/` (if exists)

**Test Cases Needed:**
- [ ] Usage tracking
- [ ] Billing calculation
- [ ] Stripe integration
- [ ] Webhook handling

**Estimated Effort:** 2-3 days

---

### 5. Database Operations (MEDIUM PRIORITY)

**Current:** Partial coverage  
**Target:** 80%+ coverage

**Files:**
- `agent_factory/database/session.py`
- `agent_factory/database/models.py`

**Test Cases Needed:**
- [ ] Database connection
- [ ] CRUD operations
- [ ] Multi-tenant isolation
- [ ] Transaction handling

**Estimated Effort:** 1-2 days

---

## Quick Wins (Low Effort, High Impact)

### 1. Add Missing Assertions
**Effort:** 1 hour  
**Impact:** Improves test quality

### 2. Add Edge Case Tests
**Effort:** 2-3 hours  
**Impact:** Catches bugs

### 3. Add Integration Tests
**Effort:** 1 day  
**Impact:** Tests real workflows

---

## Implementation Plan

### Week 1: API Endpoints
- [ ] Add tests for agent endpoints
- [ ] Add tests for workflow endpoints
- [ ] Add tests for blueprint endpoints
- **Target:** +15% coverage

### Week 2: Workflows & Billing
- [ ] Add workflow tests
- [ ] Add billing tests
- **Target:** +10% coverage

### Week 3: Database & Edge Cases
- [ ] Add database tests
- [ ] Add edge case tests
- **Target:** +5% coverage

### Week 4: Integration Tests
- [ ] Add E2E tests for critical paths
- [ ] Add integration tests
- **Target:** +5% coverage

**Total Target:** 80%+ coverage

---

## Commands

### Measure Coverage
```bash
pytest --cov=agent_factory --cov-report=html --cov-report=term
```

### View HTML Report
```bash
open htmlcov/index.html
```

### Run Specific Test File
```bash
pytest tests/test_agents.py -v
```

### Run with Coverage for Specific File
```bash
pytest tests/test_agents.py --cov=agent_factory.core.agent --cov-report=term
```

---

## Test Writing Guidelines

### Structure
```python
def test_create_agent_success():
    """Test successful agent creation"""
    # Arrange
    # Act
    # Assert
```

### Best Practices
- Test success cases
- Test error cases
- Test edge cases
- Use fixtures for setup
- Mock external dependencies
- Keep tests fast and isolated

---

**Last Updated:** 2026-10-01  
**Next Review:** [Set weekly review]

