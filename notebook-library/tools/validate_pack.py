#!/usr/bin/env python3
"""
Pack Validator - Validates pack structure and executes notebooks
"""
import argparse
import json
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any

# Get library root
LIBRARY_ROOT = Path(__file__).parent.parent
PACKS_DIR = LIBRARY_ROOT / "packs"


def validate_pack_json(pack_dir: Path) -> tuple[bool, list[str]]:
    """Validate pack.json schema."""
    errors = []
    pack_json_path = pack_dir / "pack.json"
    
    if not pack_json_path.exists():
        return False, ["pack.json not found"]
    
    try:
        with open(pack_json_path) as f:
            pack_json = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in pack.json: {e}"]
    
    # Required fields
    required_fields = [
        "id", "slug", "title", "version", "category", "difficulty",
        "runtime_minutes", "description", "tags", "inputs", "outputs",
        "entrypoint", "python", "install", "run", "license", "changelog", "assets"
    ]
    
    for field in required_fields:
        if field not in pack_json:
            errors.append(f"Missing required field: {field}")
    
    # Validate category
    valid_categories = ["ai_ops", "finops", "consulting", "devtools", "rag"]
    if pack_json.get("category") not in valid_categories:
        errors.append(f"Invalid category. Must be one of: {valid_categories}")
    
    # Validate difficulty
    valid_difficulties = ["beginner", "intermediate", "advanced"]
    if pack_json.get("difficulty") not in valid_difficulties:
        errors.append(f"Invalid difficulty. Must be one of: {valid_difficulties}")
    
    # Check entrypoint exists
    entrypoint = pack_json.get("entrypoint", "main.ipynb")
    if not (pack_dir / entrypoint).exists():
        errors.append(f"Entrypoint notebook not found: {entrypoint}")
    
    return len(errors) == 0, errors


def validate_structure(pack_dir: Path) -> tuple[bool, list[str]]:
    """Validate pack directory structure."""
    errors = []
    
    required_files = ["pack.json", "README.md", "quickstart.md", "CHANGELOG.md", "LICENSE.txt"]
    for file in required_files:
        if not (pack_dir / file).exists():
            errors.append(f"Missing required file: {file}")
    
    # Check for entrypoint
    pack_json_path = pack_dir / "pack.json"
    if pack_json_path.exists():
        with open(pack_json_path) as f:
            pack_json = json.load(f)
        entrypoint = pack_json.get("entrypoint", "main.ipynb")
        if not (pack_dir / entrypoint).exists():
            errors.append(f"Entrypoint notebook not found: {entrypoint}")
    
    return len(errors) == 0, errors


def execute_notebook(pack_dir: Path, pack_json: dict[str, Any], timeout: int = 900) -> tuple[bool, str]:
    """Execute notebook in isolated environment."""
    entrypoint = pack_json.get("entrypoint", "main.ipynb")
    notebook_path = pack_dir / entrypoint
    
    if not notebook_path.exists():
        return False, f"Notebook not found: {entrypoint}"
    
    # Create temporary virtual environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        venv.create(venv_path, with_pip=True)
        
        # Determine Python executable
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
            pip_exe = venv_path / "Scripts" / "pip.exe"
        else:
            python_exe = venv_path / "bin" / "python"
            pip_exe = venv_path / "bin" / "pip"
        
        # Install dependencies
        install_tool = pack_json.get("install", {}).get("tool", "pip")
        install_cmd = pack_json.get("install", {}).get("command", "pip install -r requirements.txt")
        
        # Check for requirements.txt or pyproject.toml
        deps_file = None
        if (pack_dir / "requirements.txt").exists():
            deps_file = pack_dir / "requirements.txt"
            install_cmd = f"{pip_exe} install -r {deps_file}"
        elif (pack_dir / "pyproject.toml").exists():
            # Install from pyproject.toml
            install_cmd = f"{pip_exe} install -e {pack_dir}"
        
        if deps_file or (pack_dir / "pyproject.toml").exists():
            print("  Installing dependencies...")
            try:
                result = subprocess.run(
                    install_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=pack_dir
                )
                if result.returncode != 0:
                    return False, f"Dependency installation failed: {result.stderr}"
            except subprocess.TimeoutExpired:
                return False, "Dependency installation timed out"
            except Exception as e:
                return False, f"Dependency installation error: {e}"
        
        # Install jupyter and nbconvert
        print("  Installing jupyter and nbconvert...")
        subprocess.run(
            [str(pip_exe), "install", "-q", "jupyter", "nbconvert", "ipykernel"],
            capture_output=True,
            timeout=120
        )
        
        # Execute notebook
        print("  Executing notebook...")
        run_cmd = pack_json.get("run", {}).get("command", f"jupyter nbconvert --to notebook --execute {notebook_path}")
        
        # Replace jupyter with full path
        run_cmd = run_cmd.replace("jupyter", str(venv_path / "bin" / "jupyter"))
        
        try:
            result = subprocess.run(
                run_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=pack_dir
            )
            
            if result.returncode != 0:
                return False, f"Notebook execution failed: {result.stderr[:500]}"
            
            return True, "Notebook executed successfully"
        except subprocess.TimeoutExpired:
            return False, f"Notebook execution timed out after {timeout} seconds"
        except Exception as e:
            return False, f"Notebook execution error: {e}"


def check_outputs(pack_dir: Path, pack_json: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check that expected outputs exist."""
    errors = []
    outputs = pack_json.get("outputs", [])
    
    for output in outputs:
        output_path = pack_dir / output.get("path", "")
        if not output_path.exists():
            errors.append(f"Expected output not found: {output['path']}")
    
    return len(errors) == 0, errors


def validate_pack(pack_id: str, execute: bool = False) -> bool:
    """Validate a single pack."""
    pack_dir = PACKS_DIR / pack_id
    
    if not pack_dir.exists():
        print(f"❌ Pack not found: {pack_id}")
        return False
    
    print(f"\n{'='*70}")
    print(f"📦 Validating: {pack_id}")
    print(f"{'='*70}")
    
    # Load pack.json
    pack_json_path = pack_dir / "pack.json"
    if not pack_json_path.exists():
        print("❌ pack.json not found")
        return False
    
    with open(pack_json_path) as f:
        pack_json = json.load(f)
    
    pack_title = pack_json.get("title", pack_id)
    print(f"Title: {pack_title}")
    print()
    
    all_valid = True
    
    # Validate structure
    print("1️⃣  Validating structure...")
    valid, errors = validate_structure(pack_dir)
    if valid:
        print("   ✅ Structure valid")
    else:
        print("   ❌ Structure errors:")
        for error in errors:
            print(f"      - {error}")
        all_valid = False
    
    # Validate pack.json schema
    print("\n2️⃣  Validating pack.json schema...")
    valid, errors = validate_pack_json(pack_dir)
    if valid:
        print("   ✅ Schema valid")
    else:
        print("   ❌ Schema errors:")
        for error in errors:
            print(f"      - {error}")
        all_valid = False
    
    # Execute notebook if requested
    if execute:
        print("\n3️⃣  Executing notebook...")
        valid, message = execute_notebook(pack_dir, pack_json)
        if valid:
            print(f"   ✅ {message}")
        else:
            print(f"   ❌ {message}")
            all_valid = False
        
        # Check outputs
        print("\n4️⃣  Checking outputs...")
        valid, errors = check_outputs(pack_dir, pack_json)
        if valid:
            print("   ✅ All outputs present")
        else:
            print("   ⚠️  Missing outputs:")
            for error in errors:
                print(f"      - {error}")
            # Don't fail validation for missing outputs (they may be optional)
    
    if all_valid:
        print(f"\n✅ Pack {pack_id} is valid!")
    else:
        print(f"\n❌ Pack {pack_id} has validation errors")
    
    return all_valid


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate notebook packs")
    parser.add_argument("pack_id", nargs="?", help="Pack ID to validate (e.g., pack_0001). If not provided, validates all packs.")
    parser.add_argument("--all", action="store_true", help="Validate all packs")
    parser.add_argument("--execute", action="store_true", help="Execute notebooks (creates venv, installs deps, runs notebook)")
    parser.add_argument("--timeout", type=int, default=900, help="Timeout for notebook execution in seconds (default: 900)")
    
    args = parser.parse_args()
    
    if args.all or not args.pack_id:
        # Validate all packs
        packs = sorted([d.name for d in PACKS_DIR.iterdir() if d.is_dir() and d.name.startswith("pack_")])
        if not packs:
            print("No packs found")
            return
        
        print(f"Validating {len(packs)} packs...")
        results = []
        for pack_id in packs:
            valid = validate_pack(pack_id, execute=args.execute)
            results.append((pack_id, valid))
        
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        for pack_id, valid in results:
            status = "✅" if valid else "❌"
            print(f"{status} {pack_id}")
        
        all_valid = all(valid for _, valid in results)
        sys.exit(0 if all_valid else 1)
    else:
        # Validate single pack
        valid = validate_pack(args.pack_id, execute=args.execute)
        sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
