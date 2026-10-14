#!/usr/bin/env python3
"""
Environment variable doctor script.

Checks for:
- Environment variables defined but never used
- Environment variables used but not defined in .env.example
- Name casing or spelling inconsistencies
- Missing required variables

Usage:
    python scripts/env-doctor.py

Environment:
    Reads from .env.example and scans codebase for usage
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def read_env_example() -> Dict[str, str]:
    """Read .env.example and extract variable names."""
    env_example_path = project_root / ".env.example"
    if not env_example_path.exists():
        print("⚠️  .env.example not found")
        return {}
    
    vars_from_example = {}
    with open(env_example_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Extract variable name (before =)
            if '=' in line:
                var_name = line.split('=')[0].strip()
                vars_from_example[var_name] = line
    
    return vars_from_example


def scan_codebase_for_env_usage() -> Dict[str, List[str]]:
    """Scan codebase for environment variable usage."""
    usage_patterns = [
        r'os\.getenv\(["\']([^"\']+)["\']',
        r'os\.environ\[["\']([^"\']+)["\']',
        r'os\.environ\.get\(["\']([^"\']+)["\']',
        r'process\.env\.([A-Z_][A-Z0-9_]*)',  # Node.js style
        r'\$\{([A-Z_][A-Z0-9_]*)\}',  # Shell style
    ]
    
    env_usage = defaultdict(list)
    
    # Directories to scan
    scan_dirs = [
        project_root / "agent_factory",
        project_root / "scripts",
        project_root / "tests",
        project_root / ".github" / "workflows",
    ]
    
    # File extensions to scan
    extensions = {'.py', '.yml', '.yaml', '.sh', '.js', '.ts', '.tsx', '.jsx'}
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        for pattern in usage_patterns:
                            matches = re.finditer(pattern, content)
                            for match in matches:
                                var_name = match.group(1)
                                # Find line number
                                line_num = content[:match.start()].count('\n') + 1
                                rel_path = file_path.relative_to(project_root)
                                env_usage[var_name].append(f"{rel_path}:{line_num}")
                except Exception as e:
                    # Skip files that can't be read
                    continue
    
    return dict(env_usage)


def check_ci_workflows() -> Dict[str, List[str]]:
    """Check GitHub Actions workflows for env var references."""
    workflow_vars = defaultdict(list)
    workflows_dir = project_root / ".github" / "workflows"
    
    if not workflows_dir.exists():
        return {}
    
    for workflow_file in workflows_dir.glob("*.yml"):
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
                # Look for secrets references
                secrets_pattern = r'\$\{\{\s*secrets\.([A-Z_][A-Z0-9_]*)\s*\}\}'
                matches = re.finditer(secrets_pattern, content)
                for match in matches:
                    var_name = match.group(1)
                    workflow_vars[var_name].append(str(workflow_file.name))
        except Exception:
            continue
    
    return dict(workflow_vars)


def normalize_var_name(name: str) -> str:
    """Normalize variable name for comparison (case-insensitive)."""
    return name.upper()


def find_similar_names(target: str, candidates: Set[str]) -> List[str]:
    """Find similar variable names (for typo detection)."""
    target_upper = target.upper()
    similar = []
    
    for candidate in candidates:
        candidate_upper = candidate.upper()
        # Check if names are similar (differ by 1-2 characters)
        if candidate_upper != target_upper:
            # Simple similarity check
            if len(candidate_upper) == len(target_upper):
                diff = sum(c1 != c2 for c1, c2 in zip(target_upper, candidate_upper))
                if diff <= 2:
                    similar.append(candidate)
    
    return similar


def main():
    """Run environment variable doctor checks."""
    print("=" * 70)
    print("Environment Variable Doctor")
    print("=" * 70)
    print()
    
    # Read .env.example
    print("📋 Reading .env.example...")
    vars_from_example = read_env_example()
    print(f"   Found {len(vars_from_example)} variables in .env.example")
    print()
    
    # Scan codebase
    print("🔍 Scanning codebase for environment variable usage...")
    env_usage = scan_codebase_for_env_usage()
    print(f"   Found {len(env_usage)} unique variables used in code")
    print()
    
    # Check CI workflows
    print("⚙️  Checking CI workflows...")
    workflow_vars = check_ci_workflows()
    print(f"   Found {len(workflow_vars)} secrets referenced in workflows")
    print()
    
    # Analysis
    print("=" * 70)
    print("Analysis Results")
    print("=" * 70)
    print()
    
    issues_found = False
    
    # 1. Variables in .env.example but not used
    print("1. Variables defined in .env.example but not used in code:")
    unused_vars = []
    for var_name in vars_from_example.keys():
        if var_name not in env_usage:
            unused_vars.append(var_name)
    
    if unused_vars:
        issues_found = True
        for var_name in sorted(unused_vars):
            print(f"   ⚠️  {var_name}")
            # Check if it's a secret (should still be documented)
            if 'SECRET' in var_name or 'KEY' in var_name or 'PASSWORD' in var_name:
                print(f"      (Note: Secret variable - should remain documented)")
    else:
        print("   ✓ All variables in .env.example are used")
    print()
    
    # 2. Variables used but not in .env.example
    print("2. Variables used in code but not in .env.example:")
    missing_vars = []
    for var_name in env_usage.keys():
        if var_name not in vars_from_example:
            missing_vars.append(var_name)
    
    if missing_vars:
        issues_found = True
        for var_name in sorted(missing_vars):
            print(f"   ❌ {var_name}")
            print(f"      Used in: {', '.join(env_usage[var_name][:3])}")
            if len(env_usage[var_name]) > 3:
                print(f"      ... and {len(env_usage[var_name]) - 3} more locations")
    else:
        print("   ✓ All used variables are documented in .env.example")
    print()
    
    # 3. Check for similar names (potential typos)
    print("3. Potential naming inconsistencies:")
    all_vars = set(vars_from_example.keys()) | set(env_usage.keys())
    normalized_map = defaultdict(list)
    for var in all_vars:
        normalized_map[normalize_var_name(var)].append(var)
    
    inconsistencies = []
    for normalized, variants in normalized_map.items():
        if len(variants) > 1:
            inconsistencies.append(variants)
    
    if inconsistencies:
        issues_found = True
        for variants in inconsistencies:
            print(f"   ⚠️  Similar names found: {', '.join(variants)}")
            print(f"      Consider standardizing to one name")
    else:
        print("   ✓ No naming inconsistencies found")
    print()
    
    # 4. CI workflow secrets not documented
    print("4. Secrets referenced in CI workflows:")
    workflow_secrets_not_doced = []
    for secret_name in workflow_vars.keys():
        if secret_name not in vars_from_example:
            workflow_secrets_not_doced.append(secret_name)
    
    if workflow_secrets_not_doced:
        issues_found = True
        for secret_name in sorted(workflow_secrets_not_doced):
            print(f"   ⚠️  {secret_name}")
            print(f"      Used in workflows: {', '.join(workflow_vars[secret_name])}")
            print(f"      (Note: CI secrets should be documented)")
    else:
        print("   ✓ All CI secrets are documented")
    print()
    
    # Summary
    print("=" * 70)
    if issues_found:
        print("⚠️  Issues found - review above")
        print()
        print("Recommendations:")
        print("  1. Add missing variables to .env.example")
        print("  2. Remove or document unused variables")
        print("  3. Standardize variable naming")
        print("  4. Document CI secrets in docs/env-and-secrets.md")
        return 1
    else:
        print("✓ No issues found - environment variables are well-managed!")
        return 0


if __name__ == '__main__':
    sys.exit(main())
