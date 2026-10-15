#!/usr/bin/env python3
"""
Blueprint Publishing Helper Script

Helps publish blueprints to the marketplace with versioning, hashing, and signing.
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


# Placeholder for signing (implement with actual signing library)
def generate_signature(content: str, private_key: str | None = None) -> str:
    """
    Generate signature for blueprint content.
    
    In production, use proper cryptographic signing (e.g., GPG, RSA).
    This is a placeholder implementation.
    """
    if private_key:
        # TODO: Implement actual signing with private_key
        # For now, return a placeholder
        return f"signature_placeholder_{hashlib.sha256(content.encode()).hexdigest()[:16]}"
    return "unsigned"


def calculate_hash(content: str) -> str:
    """Calculate SHA256 hash of content."""
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"


def load_blueprint(blueprint_path: Path) -> dict[str, Any]:
    """Load blueprint from YAML file."""
    with open(blueprint_path, 'r') as f:
        return yaml.safe_load(f)


def update_blueprints_index(
    blueprint_path: Path,
    index_path: Path,
    version: str | None = None,
    private_key: str | None = None
) -> dict[str, Any]:
    """
    Update blueprints_index.json with new blueprint.
    
    Args:
        blueprint_path: Path to blueprint.yaml
        index_path: Path to blueprints_index.json
        version: Optional version override
        private_key: Optional private key for signing
        
    Returns:
        Updated blueprint entry
    """
    # Load blueprint
    blueprint_data = load_blueprint(blueprint_path)
    blueprint_info = blueprint_data.get('blueprint', {})
    
    blueprint_id = blueprint_info.get('id')
    if not blueprint_id:
        raise ValueError("Blueprint must have an 'id' field")
    
    # Read blueprint content for hashing
    with open(blueprint_path, 'r') as f:
        blueprint_content = f.read()
    
    # Calculate hash
    blueprint_hash = calculate_hash(blueprint_content)
    
    # Generate signature
    signature = generate_signature(blueprint_content, private_key)
    
    # Determine version
    blueprint_version = version or blueprint_info.get('version', '1.0.0')
    
    # Create entry
    entry = {
        "id": blueprint_id,
        "name": blueprint_info.get('name', blueprint_id),
        "version": blueprint_version,
        "description": blueprint_info.get('description', ''),
        "author": blueprint_info.get('author', 'Unknown'),
        "category": blueprint_info.get('category', 'general'),
        "tags": blueprint_info.get('tags', []),
        "pricing": blueprint_info.get('pricing', {
            "model": "free",
            "price": 0.0,
            "currency": "USD"
        }),
        "download_url": f"https://github.com/agentfactory/platform/raw/main/blueprints/{blueprint_id}/blueprint.yaml",
        "hash": blueprint_hash,
        "signature": signature,
        "compatibility": {
            "agent_factory_version": ">=0.1.0",
            "python_version": ">=3.8"
        },
        "metadata": blueprint_info.get('metadata', {})
    }
    
    # Load existing index
    if index_path.exists():
        with open(index_path, 'r') as f:
            index = json.load(f)
    else:
        index = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat() + "Z",
            "blueprints": []
        }
    
    # Update or add blueprint entry
    blueprints = index.get('blueprints', [])
    existing_idx = next(
        (i for i, bp in enumerate(blueprints) if bp['id'] == blueprint_id),
        None
    )
    
    if existing_idx is not None:
        # Update existing
        blueprints[existing_idx] = entry
        print(f"✅ Updated blueprint '{blueprint_id}' in index")
    else:
        # Add new
        blueprints.append(entry)
        print(f"✅ Added blueprint '{blueprint_id}' to index")
    
    index['blueprints'] = blueprints
    index['last_updated'] = datetime.now().isoformat() + "Z"
    
    # Write updated index
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    return entry


def main():
    parser = argparse.ArgumentParser(
        description="Publish blueprint to marketplace index"
    )
    parser.add_argument(
        "blueprint_path",
        type=Path,
        help="Path to blueprint.yaml file"
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("blueprints_index.json"),
        help="Path to blueprints_index.json (default: blueprints_index.json)"
    )
    parser.add_argument(
        "--version",
        help="Override blueprint version"
    )
    parser.add_argument(
        "--private-key",
        help="Private key file for signing (optional)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify blueprint before publishing"
    )
    
    args = parser.parse_args()
    
    if not args.blueprint_path.exists():
        print(f"❌ Error: Blueprint file not found: {args.blueprint_path}")
        sys.exit(1)
    
    # Verify blueprint if requested
    if args.verify:
        try:
            from agent_factory.core.blueprint import Blueprint
            blueprint = Blueprint.from_yaml(str(args.blueprint_path))
            print(f"✅ Blueprint validation passed: {blueprint.id}")
        except Exception as e:
            print(f"❌ Blueprint validation failed: {e}")
            sys.exit(1)
    
    # Load private key if provided
    private_key = None
    if args.private_key:
        with open(args.private_key, 'r') as f:
            private_key = f.read()
    
    try:
        entry = update_blueprints_index(
            args.blueprint_path,
            args.index,
            version=args.version,
            private_key=private_key
        )
        
        print("\n📦 Blueprint published:")
        print(f"   ID: {entry['id']}")
        print(f"   Version: {entry['version']}")
        print(f"   Hash: {entry['hash']}")
        print(f"   Signature: {entry['signature'][:50]}...")
        print(f"\n✅ Index updated: {args.index}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
