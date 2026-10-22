#!/usr/bin/env python3
"""
Documentation synchronization script.

Ensures documentation stays in sync with code:
- API documentation matches endpoints
- Schema documentation matches models
- Environment variables match .env.example
- CI/CD documentation matches workflows

Usage:
    python scripts/doc-sync.py [--check] [--fix]

Options:
    --check: Only check for inconsistencies (don't fix)
    --fix: Automatically fix inconsistencies where possible
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_api_docs() -> list[str]:
    """Check if API documentation matches actual endpoints."""
    issues = []
    
    # Find all API route files
    routes_dir = project_root / "agent_factory" / "api" / "routes"
    if not routes_dir.exists():
        return issues
    
    # Scan for route definitions
    endpoints = defaultdict(list)
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
        
        try:
            with open(route_file) as f:
                content = f.read()
                # Find router decorators
                route_pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
                matches = re.finditer(route_pattern, content)
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    endpoints[route_file.stem].append(f"{method} {path}")
        except Exception as e:
            issues.append(f"Error reading {route_file}: {e}")
    
    # Check if docs/api.md exists and mentions these endpoints
    api_doc = project_root / "docs" / "api.md"
    if api_doc.exists():
        try:
            with open(api_doc) as f:
                doc_content = f.read()
                # Check if endpoints are documented
                for route_file, endpoint_list in endpoints.items():
                    for endpoint in endpoint_list:
                        # Simple check - endpoint path should be mentioned
                        if endpoint.split()[1] not in doc_content:
                            issues.append(f"Endpoint {endpoint} in {route_file} not documented in docs/api.md")
        except Exception as e:
            issues.append(f"Error reading docs/api.md: {e}")
    else:
        issues.append("docs/api.md not found - API documentation missing")
    
    return issues


def check_env_docs() -> list[str]:
    """Check if environment variable documentation matches .env.example."""
    issues = []
    
    env_example = project_root / ".env.example"
    env_doc = project_root / "docs" / "env-and-secrets.md"
    
    if not env_example.exists():
        issues.append(".env.example not found")
        return issues
    
    # Read .env.example
    env_vars = set()
    with open(env_example) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                var_name = line.split('=')[0].strip()
                env_vars.add(var_name)
    
    # Check if documented
    if env_doc.exists():
        try:
            with open(env_doc) as f:
                doc_content = f.read()
                missing_docs = []
                for var in env_vars:
                    if var not in doc_content:
                        missing_docs.append(var)
                if missing_docs:
                    issues.append(f"Environment variables not documented: {', '.join(missing_docs[:5])}")
        except Exception as e:
            issues.append(f"Error reading docs/env-and-secrets.md: {e}")
    else:
        issues.append("docs/env-and-secrets.md not found - environment variable documentation missing")
    
    return issues


def check_schema_docs() -> list[str]:
    """Check if schema documentation matches database models."""
    issues = []
    
    models_file = project_root / "agent_factory" / "database" / "models.py"
    schema_doc = project_root / "docs" / "data-model-overview.md"
    
    if not models_file.exists():
        issues.append("agent_factory/database/models.py not found")
        return issues
    
    # Read models
    tables = set()
    try:
        with open(models_file) as f:
            content = f.read()
            # Find table definitions
            table_pattern = r'__tablename__\s*=\s*["\']([^"\']+)["\']'
            matches = re.finditer(table_pattern, content)
            for match in matches:
                tables.add(match.group(1))
    except Exception as e:
        issues.append(f"Error reading models.py: {e}")
        return issues
    
    # Check if documented
    if schema_doc.exists():
        try:
            with open(schema_doc) as f:
                doc_content = f.read()
                missing_docs = []
                for table in tables:
                    if table not in doc_content:
                        missing_docs.append(table)
                if missing_docs:
                    issues.append(f"Tables not documented: {', '.join(missing_docs[:5])}")
        except Exception as e:
            issues.append(f"Error reading docs/data-model-overview.md: {e}")
    else:
        issues.append("docs/data-model-overview.md not found - schema documentation missing")
    
    return issues


def check_ci_docs() -> list[str]:
    """Check if CI/CD documentation matches workflows."""
    issues = []
    
    workflows_dir = project_root / ".github" / "workflows"
    ci_doc = project_root / "docs" / "ci-overview.md"
    
    if not workflows_dir.exists():
        return issues
    
    # Find workflow files
    workflows = set()
    for workflow_file in workflows_dir.glob("*.yml"):
        workflows.add(workflow_file.stem)
    
    # Check if documented
    if ci_doc.exists():
        try:
            with open(ci_doc) as f:
                doc_content = f.read()
                missing_docs = []
                for workflow in workflows:
                    if workflow not in doc_content:
                        missing_docs.append(workflow)
                if missing_docs:
                    issues.append(f"Workflows not documented: {', '.join(missing_docs[:3])}")
        except Exception as e:
            issues.append(f"Error reading docs/ci-overview.md: {e}")
    else:
        issues.append("docs/ci-overview.md not found - CI/CD documentation missing")
    
    return issues


def main():
    """Run documentation synchronization checks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Documentation synchronization checker")
    parser.add_argument("--check", action="store_true", help="Only check for inconsistencies")
    parser.add_argument("--fix", action="store_true", help="Automatically fix inconsistencies")
    args = parser.parse_args()
    
    print("=" * 70)
    print("Documentation Synchronization Check")
    print("=" * 70)
    print()
    
    all_issues = []
    
    # Check API documentation
    print("Checking API documentation...")
    api_issues = check_api_docs()
    if api_issues:
        all_issues.extend(api_issues)
        for issue in api_issues:
            print(f"  ⚠️  {issue}")
    else:
        print("  ✓ API documentation in sync")
    print()
    
    # Check environment variable documentation
    print("Checking environment variable documentation...")
    env_issues = check_env_docs()
    if env_issues:
        all_issues.extend(env_issues)
        for issue in env_issues:
            print(f"  ⚠️  {issue}")
    else:
        print("  ✓ Environment variable documentation in sync")
    print()
    
    # Check schema documentation
    print("Checking schema documentation...")
    schema_issues = check_schema_docs()
    if schema_issues:
        all_issues.extend(schema_issues)
        for issue in schema_issues:
            print(f"  ⚠️  {issue}")
    else:
        print("  ✓ Schema documentation in sync")
    print()
    
    # Check CI/CD documentation
    print("Checking CI/CD documentation...")
    ci_issues = check_ci_docs()
    if ci_issues:
        all_issues.extend(ci_issues)
        for issue in ci_issues:
            print(f"  ⚠️  {issue}")
    else:
        print("  ✓ CI/CD documentation in sync")
    print()
    
    # Summary
    print("=" * 70)
    if all_issues:
        print(f"⚠️  Found {len(all_issues)} documentation inconsistencies")
        print()
        if args.fix:
            print("Auto-fix not implemented yet. Please update documentation manually.")
        else:
            print("Run with --fix to attempt automatic fixes (not yet implemented)")
        return 1
    else:
        print("✓ All documentation is synchronized!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
