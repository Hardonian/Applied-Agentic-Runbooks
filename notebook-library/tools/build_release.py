#!/usr/bin/env python3
"""
Build Release - Creates release zips for packs and library
"""
import argparse
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

# Get library root
LIBRARY_ROOT = Path(__file__).parent.parent
PACKS_DIR = LIBRARY_ROOT / "packs"
DIST_DIR = LIBRARY_ROOT / "dist"


def get_pack_metadata(pack_dir: Path) -> dict[str, Any]:
    """Load pack metadata from pack.json."""
    pack_json_path = pack_dir / "pack.json"
    if not pack_json_path.exists():
        return None
    
    with open(pack_json_path) as f:
        return json.load(f)


def create_pack_zip(pack_dir: Path, pack_json: dict[str, Any], output_dir: Path) -> Path:
    """Create zip file for a single pack."""
    pack_id = pack_json["id"]
    pack_slug = pack_json["slug"]
    version = pack_json["version"]
    
    zip_filename = f"{pack_slug}-v{version}.zip"
    zip_path = output_dir / zip_filename
    
    # Files/directories to include
    include_patterns = [
        "main.ipynb",
        "*.ipynb",
        "README.md",
        "quickstart.md",
        "CHANGELOG.md",
        "LICENSE.txt",
        "pack.json",
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        "data/**",
        "assets/**",
    ]
    
    # Files/directories to exclude
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".env",
        "*.log",
        ".git",
        ".gitignore",
        "outputs/**",  # Exclude outputs (they're generated)
    ]
    
    print(f"  📦 Creating {zip_filename}...")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in pack_dir.rglob("*"):
            if file_path.is_dir():
                continue
            
            rel_path = file_path.relative_to(pack_dir)
            rel_str = str(rel_path)
            
            # Check if excluded
            excluded = False
            for pattern in exclude_patterns:
                if pattern.replace("**", "") in rel_str or rel_str.startswith(pattern.replace("**", "").rstrip("/")):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            # Check if included
            included = False
            for pattern in include_patterns:
                if pattern.replace("**", "") in rel_str or rel_str.startswith(pattern.replace("**", "").rstrip("/")):
                    included = True
                    break
                if "*" in pattern:
                    import fnmatch
                    if fnmatch.fnmatch(rel_str, pattern):
                        included = True
                        break
            
            if included or any(rel_str.endswith(ext) for ext in [".md", ".txt", ".json", ".ipynb", ".toml", ".png", ".svg", ".html"]):
                zf.write(file_path, rel_str)
                print(f"     + {rel_str}")
    
    print(f"  ✅ Created: {zip_path}")
    return zip_path


def create_library_zip(packs: list[dict[str, Any]], output_dir: Path) -> Path:
    """Create library release zip with all packs."""
    timestamp = datetime.now().strftime("%Y%m%d")
    zip_filename = f"notebook-library-{timestamp}.zip"
    zip_path = output_dir / zip_filename
    
    print(f"\n📚 Creating library release: {zip_filename}...")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add library.json
        library_json_path = LIBRARY_ROOT / "library.json"
        if library_json_path.exists():
            zf.write(library_json_path, "library.json")
            print("  + library.json")
        
        # Add LICENSING.md if exists
        licensing_path = LIBRARY_ROOT / "LICENSING.md"
        if licensing_path.exists():
            zf.write(licensing_path, "LICENSING.md")
            print("  + LICENSING.md")
        
        # Add each pack
        for pack_json in packs:
            pack_id = pack_json["id"]
            pack_dir = PACKS_DIR / pack_id
            
            if not pack_dir.exists():
                continue
            
            # Create pack zip first
            pack_zip = create_pack_zip(pack_dir, pack_json, output_dir)
            
            # Add pack zip to library zip
            zf.write(pack_zip, f"packs/{pack_zip.name}")
            print(f"  + packs/{pack_zip.name}")
    
    print(f"\n✅ Library release created: {zip_path}")
    return zip_path


def build_release(pack_id: str | None = None) -> list[Path]:
    """Build release zip(s)."""
    DIST_DIR.mkdir(exist_ok=True)
    
    created_zips = []
    
    if pack_id:
        # Build single pack
        pack_dir = PACKS_DIR / pack_id
        if not pack_dir.exists():
            print(f"❌ Pack not found: {pack_id}")
            return []
        
        pack_json = get_pack_metadata(pack_dir)
        if not pack_json:
            print(f"❌ Could not load pack.json for {pack_id}")
            return []
        
        print(f"\n{'='*70}")
        print(f"📦 Building Release: {pack_id}")
        print(f"{'='*70}")
        
        zip_path = create_pack_zip(pack_dir, pack_json, DIST_DIR)
        created_zips.append(zip_path)
    else:
        # Build all packs and library
        print(f"\n{'='*70}")
        print("📚 Building Library Release")
        print(f"{'='*70}")
        
        # Get all packs
        packs = []
        for pack_dir in sorted(PACKS_DIR.iterdir()):
            if not pack_dir.is_dir() or not pack_dir.name.startswith("pack_"):
                continue
            
            pack_json = get_pack_metadata(pack_dir)
            if pack_json:
                packs.append(pack_json)
                # Also create individual pack zips
                zip_path = create_pack_zip(pack_dir, pack_json, DIST_DIR)
                created_zips.append(zip_path)
        
        # Create library zip
        if packs:
            library_zip = create_library_zip(packs, DIST_DIR)
            created_zips.append(library_zip)
    
    print(f"\n{'='*70}")
    print("✅ Build complete!")
    print(f"{'='*70}")
    print(f"\nCreated {len(created_zips)} zip file(s):")
    for zip_path in created_zips:
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"  📦 {zip_path.name} ({size_mb:.2f} MB)")
    
    return created_zips


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build release zips for packs")
    parser.add_argument("pack_id", nargs="?", help="Pack ID to build (e.g., pack_0001). If not provided, builds all packs and library.")
    
    args = parser.parse_args()
    
    build_release(args.pack_id)


if __name__ == "__main__":
    main()
