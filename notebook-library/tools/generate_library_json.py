#!/usr/bin/env python3
"""
Generate Library JSON - Creates library.json index from all packs
"""
import json
from pathlib import Path
from typing import Any

# Get library root
LIBRARY_ROOT = Path(__file__).parent.parent
PACKS_DIR = LIBRARY_ROOT / "packs"
LIBRARY_JSON_PATH = LIBRARY_ROOT / "library.json"


def load_pack_metadata(pack_dir: Path) -> dict[str, Any] | None:
    """Load pack metadata."""
    pack_json_path = pack_dir / "pack.json"
    if not pack_json_path.exists():
        return None
    
    try:
        with open(pack_json_path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {pack_json_path}: {e}")
        return None


def generate_library_json() -> dict[str, Any]:
    """Generate library.json from all packs."""
    packs = []
    
    # Scan all pack directories
    for pack_dir in sorted(PACKS_DIR.iterdir()):
        if not pack_dir.is_dir() or not pack_dir.name.startswith("pack_"):
            continue
        
        pack_metadata = load_pack_metadata(pack_dir)
        if pack_metadata:
            # Include minimal metadata for library index
            pack_info = {
                "id": pack_metadata.get("id"),
                "slug": pack_metadata.get("slug"),
                "title": pack_metadata.get("title"),
                "version": pack_metadata.get("version"),
                "category": pack_metadata.get("category"),
                "difficulty": pack_metadata.get("difficulty"),
                "runtime_minutes": pack_metadata.get("runtime_minutes"),
                "description": pack_metadata.get("description"),
                "tags": pack_metadata.get("tags", []),
            }
            packs.append(pack_info)
    
    library_json = {
        "version": "1.0.0",
        "generated_at": None,  # Will be set by script
        "packs": packs,
        "total_packs": len(packs),
    }
    
    return library_json


def main():
    """Main entry point."""
    from datetime import datetime
    
    print("📚 Generating library.json...")
    
    library_json = generate_library_json()
    library_json["generated_at"] = datetime.now().isoformat()
    
    # Write library.json
    with open(LIBRARY_JSON_PATH, "w") as f:
        json.dump(library_json, f, indent=2)
    
    print(f"✅ Generated library.json with {library_json['total_packs']} packs")
    print(f"   Location: {LIBRARY_JSON_PATH}")


if __name__ == "__main__":
    main()
