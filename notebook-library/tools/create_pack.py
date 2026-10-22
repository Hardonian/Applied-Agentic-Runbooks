#!/usr/bin/env python3
"""
Notebook Pack Generator - Creates a new pack from template
"""
import json
import shutil
import sys
from pathlib import Path
from typing import Any

# Get library root
LIBRARY_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = LIBRARY_ROOT / "templates" / "pack_template"
PACKS_DIR = LIBRARY_ROOT / "packs"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    return text.lower().replace(" ", "-").replace("_", "-")


def get_pack_id() -> str:
    """Get next available pack ID."""
    existing_packs = sorted([d.name for d in PACKS_DIR.iterdir() if d.is_dir() and d.name.startswith("pack_")])
    if not existing_packs:
        return "pack_0001"
    
    last_id = existing_packs[-1]
    try:
        num = int(last_id.split("_")[1])
        return f"pack_{num+1:04d}"
    except (ValueError, IndexError):
        return "pack_0001"


def prompt_user() -> dict[str, Any]:
    """Prompt user for pack details."""
    print("=" * 70)
    print("📦 NOTEBOOK PACK GENERATOR")
    print("=" * 70)
    print()
    
    pack_id = get_pack_id()
    print(f"Pack ID: {pack_id}")
    
    title = input("Pack title: ").strip()
    if not title:
        print("Error: Title is required")
        sys.exit(1)
    
    slug = input(f"Pack slug [{slugify(title)}]: ").strip() or slugify(title)
    
    print("\nCategories: ai_ops, finops, consulting, devtools, rag")
    category = input("Category [ai_ops]: ").strip() or "ai_ops"
    
    print("\nDifficulty levels: beginner, intermediate, advanced")
    difficulty = input("Difficulty [beginner]: ").strip() or "beginner"
    
    runtime = input("Runtime in minutes [15]: ").strip() or "15"
    try:
        runtime_minutes = int(runtime)
    except ValueError:
        runtime_minutes = 15
    
    description = input("Description: ").strip() or f"{title} - A notebook pack for {category}"
    
    tags_input = input("Tags (comma-separated): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
    
    return {
        "id": pack_id,
        "slug": slug,
        "title": title,
        "category": category,
        "difficulty": difficulty,
        "runtime_minutes": runtime_minutes,
        "description": description,
        "tags": tags,
    }


def create_pack(metadata: dict[str, Any]) -> Path:
    """Create pack from template."""
    pack_id = metadata["id"]
    pack_dir = PACKS_DIR / pack_id
    
    if pack_dir.exists():
        print(f"Error: Pack {pack_id} already exists")
        sys.exit(1)
    
    # Copy template
    print(f"\n📁 Creating pack directory: {pack_dir}")
    shutil.copytree(TEMPLATE_DIR, pack_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    
    # Create required directories
    (pack_dir / "data").mkdir(exist_ok=True)
    (pack_dir / "outputs").mkdir(exist_ok=True)
    (pack_dir / "assets").mkdir(exist_ok=True)
    
    # Update pack.json
    pack_json_path = pack_dir / "pack.json"
    with open(pack_json_path) as f:
        pack_json = json.load(f)
    
    pack_json.update({
        "id": metadata["id"],
        "slug": metadata["slug"],
        "title": metadata["title"],
        "category": metadata["category"],
        "difficulty": metadata["difficulty"],
        "runtime_minutes": metadata["runtime_minutes"],
        "description": metadata["description"],
        "tags": metadata["tags"],
    })
    
    with open(pack_json_path, "w") as f:
        json.dump(pack_json, f, indent=2)
    
    # Update pyproject.toml
    pyproject_path = pack_dir / "pyproject.toml"
    pyproject_content = pyproject_path.read_text()
    pyproject_content = pyproject_content.replace("pack-slug-template", metadata["slug"])
    pyproject_content = pyproject_content.replace("Template pack description", metadata["description"])
    pyproject_path.write_text(pyproject_content)
    
    # Update README.md
    readme_path = pack_dir / "README.md"
    readme_content = readme_path.read_text()
    readme_content = readme_content.replace("Pack Title Template", metadata["title"])
    readme_content = readme_content.replace("Template description", metadata["description"])
    readme_path.write_text(readme_content)
    
    # Update CHANGELOG.md
    changelog_path = pack_dir / "CHANGELOG.md"
    changelog_content = changelog_path.read_text()
    changelog_content = changelog_content.replace("YYYY-MM-DD", "2025-01-XX")
    changelog_path.write_text(changelog_content)
    
    print("✅ Pack created successfully!")
    print(f"\n📂 Location: {pack_dir}")
    print("\n📝 Next steps:")
    print(f"   1. Edit {pack_dir / 'main.ipynb'} with your notebook content")
    print(f"   2. Update {pack_dir / 'pack.json'} with inputs/outputs")
    print(f"   3. Add sample data to {pack_dir / 'data'}/")
    print(f"   4. Run: python tools/validate_pack.py {pack_id}")
    
    return pack_dir


def main():
    """Main entry point."""
    metadata = prompt_user()
    create_pack(metadata)


if __name__ == "__main__":
    main()
