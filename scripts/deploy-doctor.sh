#!/bin/bash
# Deploy Doctor - Diagnostic script for deployment configuration
# Checks for common misconfigurations in CI/CD and deployment setup

set -e

echo "🔍 Deploy Doctor - Deployment Configuration Diagnostics"
echo "========================================================"
echo ""

ERRORS=0
WARNINGS=0
INFO=0

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

check_error() {
    echo -e "${RED}❌ $1${NC}"
    ERRORS=$((ERRORS + 1))
}

check_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

check_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
    INFO=$((INFO + 1))
}

check_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

echo "1. Checking GitHub Actions Workflows..."
echo "----------------------------------------"

# Check for Vercel workflows
if [ -f ".github/workflows/deploy-vercel-preview.yml" ]; then
    check_success "Vercel Preview workflow exists"
else
    check_error "Vercel Preview workflow missing (.github/workflows/deploy-vercel-preview.yml)"
fi

if [ -f ".github/workflows/deploy-vercel-production.yml" ]; then
    check_success "Vercel Production workflow exists"
else
    check_error "Vercel Production workflow missing (.github/workflows/deploy-vercel-production.yml)"
fi

# Check workflow triggers
if grep -q "pull_request:" .github/workflows/deploy-vercel-preview.yml 2>/dev/null; then
    check_success "Preview workflow has pull_request trigger"
else
    check_warning "Preview workflow may be missing pull_request trigger"
fi

if grep -q "branches:.*main" .github/workflows/deploy-vercel-production.yml 2>/dev/null; then
    check_success "Production workflow triggers on main branch"
else
    check_warning "Production workflow may not trigger on main branch"
fi

echo ""
echo "2. Checking Vercel Configuration..."
echo "------------------------------------"

# Check for vercel.json
if [ -f "vercel.json" ]; then
    check_success "vercel.json found in root"
elif [ -f "deployment/vercel.json" ]; then
    check_warning "vercel.json found in deployment/ subdirectory (may need to be in root or configure Vercel project root)"
    check_info "If deployments fail, try moving vercel.json to root or configure Vercel project root directory"
else
    check_error "vercel.json not found (needed for Vercel deployments)"
fi

# Check vercel.json content
if [ -f "vercel.json" ] || [ -f "deployment/vercel.json" ]; then
    VERCEL_JSON=$(find . -name "vercel.json" -type f | head -1)
    if grep -q "@vercel/python" "$VERCEL_JSON" 2>/dev/null; then
        check_success "vercel.json configured for Python"
    else
        check_warning "vercel.json may not be configured for Python (@vercel/python)"
    fi
    
    if grep -q "PYTHON_VERSION" "$VERCEL_JSON" 2>/dev/null; then
        PYTHON_VERSION=$(grep -o '"PYTHON_VERSION": "[^"]*"' "$VERCEL_JSON" | cut -d'"' -f4)
        check_info "Python version in vercel.json: $PYTHON_VERSION"
    fi
fi

echo ""
echo "3. Checking Python Dependencies..."
echo "------------------------------------"

# Check for requirements.txt
if [ -f "apps/research_assistant_app/requirements.txt" ]; then
    check_success "requirements.txt found for demo app"
else
    check_warning "requirements.txt not found for demo app (apps/research_assistant_app/requirements.txt)"
fi

# Check Python version consistency
if [ -f "pyproject.toml" ]; then
    PYTHON_REQUIRES=$(grep "requires-python" pyproject.toml | sed 's/.*= *"\(.*\)".*/\1/' || echo "")
    if [ -n "$PYTHON_REQUIRES" ]; then
        check_info "Python version requirement in pyproject.toml: $PYTHON_REQUIRES"
    fi
fi

echo ""
echo "4. Checking Environment Variables..."
echo "-------------------------------------"

# Check .env.example
if [ -f ".env.example" ]; then
    check_success ".env.example exists"
    
    # Check for Vercel-related vars
    if grep -q "VERCEL" .env.example; then
        check_info ".env.example contains Vercel variables (note: Vercel uses dashboard, not .env)"
    fi
    
    # Check for required vars
    REQUIRED_VARS=("DATABASE_URL" "OPENAI_API_KEY" "JWT_SECRET_KEY")
    for VAR in "${REQUIRED_VARS[@]}"; do
        if grep -q "^$VAR=" .env.example; then
            check_success "$VAR documented in .env.example"
        else
            check_warning "$VAR not found in .env.example"
        fi
    done
else
    check_warning ".env.example not found"
fi

echo ""
echo "5. Checking Documentation..."
echo "----------------------------"

DOCS=(
    "docs/deploy-strategy.md"
    "docs/env-and-secrets.md"
    "docs/vercel-troubleshooting.md"
    "docs/deploy-reliability-plan.md"
)

for DOC in "${DOCS[@]}"; do
    if [ -f "$DOC" ]; then
        check_success "$DOC exists"
    else
        check_warning "$DOC missing"
    fi
done

echo ""
echo "6. Checking Workflow Configuration Issues..."
echo "--------------------------------------------"

# Check for deployment workflows
if [ -f ".github/workflows/deploy-preview.yml" ] && [ -f ".github/workflows/deploy-vercel-preview.yml" ]; then
    check_success "Preview deployment workflows configured (Render & Vercel)"
fi

if [ -f ".github/workflows/deploy-production.yml" ] && [ -f ".github/workflows/deploy-vercel-production.yml" ]; then
    check_success "Production deployment workflows configured (Render/K8s & Vercel)"
fi

# Check for path filters that might skip deploys
if grep -q "paths-ignore:" .github/workflows/deploy-vercel-production.yml 2>/dev/null; then
    check_info "Production workflow has paths-ignore filters (check if they're too restrictive)"
fi

echo ""
echo "7. Checking for Common Issues..."
echo "---------------------------------"

# Check if vercel.json references correct paths
if [ -f "vercel.json" ] || [ -f "deployment/vercel.json" ]; then
    VERCEL_JSON=$(find . -name "vercel.json" -type f | head -1)
    if grep -q "apps/research_assistant_app" "$VERCEL_JSON" 2>/dev/null; then
        if [ ! -f "apps/research_assistant_app/main.py" ]; then
            check_error "vercel.json references apps/research_assistant_app/main.py but file doesn't exist"
        else
            check_success "vercel.json references valid path (apps/research_assistant_app/main.py)"
        fi
    fi
fi

# Check for Node.js version in workflows (Vercel CLI needs Node)
if grep -q "setup-node" .github/workflows/deploy-vercel-*.yml 2>/dev/null; then
    check_success "Workflows install Node.js for Vercel CLI"
else
    check_error "Workflows may be missing Node.js setup (needed for Vercel CLI)"
fi

echo ""
echo "8. GitHub Secrets Checklist..."
echo "-------------------------------"
echo ""
echo "Required GitHub Secrets (set in Repository Settings → Secrets → Actions):"
echo ""
echo "  [ ] VERCEL_TOKEN - Vercel API token"
echo "       Get from: https://vercel.com/account/tokens"
echo ""
echo "  [ ] VERCEL_ORG_ID - Vercel organization/team ID"
echo "       Get from: Vercel Dashboard → Team Settings → General"
echo ""
echo "  [ ] VERCEL_PROJECT_ID - Vercel project ID"
echo "       Get from: Vercel Dashboard → Project → Settings → General"
echo ""
echo "  [ ] VERCEL_PRODUCTION_URL - Production URL (optional)"
echo "       For notifications and smoke tests"
echo ""
check_info "You cannot verify secrets from this script - check GitHub repository settings"

echo ""
echo "9. Vercel Dashboard Checklist..."
echo "-------------------------------"
echo ""
echo "Vercel Project Configuration:"
echo ""
echo "  [ ] Project linked to correct GitHub repository"
echo "  [ ] Git Integration disabled (if using GitHub Actions)"
echo "       OR Git Integration enabled (if NOT using GitHub Actions)"
echo ""
echo "  [ ] Root Directory configured correctly"
echo "       If vercel.json is in root: root directory = /"
echo "       If vercel.json is in deployment/: root directory = deployment/"
echo ""
echo "Environment Variables (Vercel Dashboard → Project → Settings → Environment Variables):"
echo ""
echo "  Preview Environment:"
echo "    [ ] DATABASE_URL (if using database)"
echo "    [ ] OPENAI_API_KEY or ANTHROPIC_API_KEY"
echo "    [ ] JWT_SECRET_KEY (if using auth)"
echo ""
echo "  Production Environment:"
echo "    [ ] DATABASE_URL (production value)"
echo "    [ ] OPENAI_API_KEY or ANTHROPIC_API_KEY (production)"
echo "    [ ] JWT_SECRET_KEY (production value)"
echo "    [ ] DEBUG=false"
echo "    [ ] LOG_LEVEL=INFO"
echo ""
check_info "You cannot verify Vercel settings from this script - check Vercel dashboard"

echo ""
echo "========================================================"
echo "Summary"
echo "========================================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Verify GitHub Secrets are set (see section 8)"
    echo "2. Verify Vercel Dashboard configuration (see section 9)"
    echo "3. Create a test PR to trigger Preview deployment"
    echo "4. Push to main to trigger Production deployment"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Found $WARNINGS warning(s), $INFO info message(s)${NC}"
    echo ""
    echo "Review warnings above and address as needed."
    echo "Deployment may still work, but warnings should be resolved."
    exit 0
else
    echo -e "${RED}❌ Found $ERRORS error(s), $WARNINGS warning(s), $INFO info message(s)${NC}"
    echo ""
    echo "Errors must be fixed before deployments will work."
    echo "Review errors above and fix them."
    exit 1
fi
