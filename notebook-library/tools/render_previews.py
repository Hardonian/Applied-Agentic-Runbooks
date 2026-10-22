#!/usr/bin/env python3
"""
Render Previews - Generate HTML previews and cover images for packs
"""
import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

# Try to import PIL for image generation
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Get library root
LIBRARY_ROOT = Path(__file__).parent.parent
PACKS_DIR = LIBRARY_ROOT / "packs"


def generate_cover_image(pack_dir: Path, pack_json: dict[str, Any]) -> Path:
    """Generate cover image for pack."""
    assets_dir = pack_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    cover_path = assets_dir / "cover.png"
    
    if HAS_PIL:
        # Create a simple cover image
        width, height = 800, 400
        img = Image.new("RGB", (width, height), color="#1e293b")
        draw = ImageDraw.Draw(img)
        
        # Title
        title = pack_json.get("title", "Notebook Pack")
        try:
            # Try to use a larger font
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw title
        bbox = draw.textbbox((0, 0), title, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = height // 2 - text_height - 20
        draw.text((x, y), title, fill="#ffffff", font=font_large)
        
        # Draw category
        category = pack_json.get("category", "").upper()
        bbox = draw.textbbox((0, 0), category, font=font_small)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = height // 2 + 20
        draw.text((x, y), category, fill="#94a3b8", font=font_small)
        
        img.save(cover_path)
        print(f"  ✅ Generated cover image: {cover_path}")
    else:
        # Create a simple SVG placeholder
        svg_content = f'''<svg width="800" height="400" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="400" fill="#1e293b"/>
  <text x="400" y="180" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="#ffffff" text-anchor="middle">{pack_json.get("title", "Notebook Pack")}</text>
  <text x="400" y="240" font-family="Arial, sans-serif" font-size="24" fill="#94a3b8" text-anchor="middle">{pack_json.get("category", "").upper()}</text>
</svg>'''
        svg_path = assets_dir / "cover.svg"
        svg_path.write_text(svg_content)
        print(f"  ✅ Generated cover SVG: {svg_path}")
        # Also create a note about PNG
        cover_path.write_text("Cover image not generated (PIL not available). See cover.svg")
    
    return cover_path


def generate_flow_diagram(pack_dir: Path, pack_json: dict[str, Any]) -> Path:
    """Generate flow diagram SVG."""
    assets_dir = pack_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    flow_path = assets_dir / "flow.svg"
    
    inputs = pack_json.get("inputs", [])
    outputs = pack_json.get("outputs", [])
    
    # Create simple flow diagram
    input_names = [inp.get("name", "Input") for inp in inputs[:3]]  # Limit to 3
    output_names = [out.get("name", "Output") for out in outputs[:3]]  # Limit to 3
    
    svg_content = '''<svg width="600" height="200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#64748b"/>
    </marker>
  </defs>
  
  <!-- Inputs -->
  <g id="inputs">
    <text x="50" y="30" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#334155">Inputs</text>
'''
    
    y_offset = 50
    for i, inp_name in enumerate(input_names):
        svg_content += f'    <rect x="20" y="{y_offset + i*40}" width="100" height="30" fill="#cbd5e1" stroke="#64748b" rx="4"/>\n'
        svg_content += f'    <text x="70" y="{y_offset + i*40 + 20}" font-family="Arial, sans-serif" font-size="12" fill="#1e293b" text-anchor="middle">{inp_name[:15]}</text>\n'
    
    svg_content += '''  </g>
  
  <!-- Notebook -->
  <g id="notebook">
    <rect x="250" y="80" width="100" height="40" fill="#3b82f6" stroke="#1e40af" rx="4"/>
    <text x="300" y="105" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#ffffff" text-anchor="middle">Notebook</text>
  </g>
  
  <!-- Outputs -->
  <g id="outputs">
    <text x="500" y="30" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#334155">Outputs</text>
'''
    
    for i, out_name in enumerate(output_names):
        svg_content += f'    <rect x="480" y="{y_offset + i*40}" width="100" height="30" fill="#cbd5e1" stroke="#64748b" rx="4"/>\n'
        svg_content += f'    <text x="530" y="{y_offset + i*40 + 20}" font-family="Arial, sans-serif" font-size="12" fill="#1e293b" text-anchor="middle">{out_name[:15]}</text>\n'
    
    svg_content += '''  </g>
  
  <!-- Arrows -->
  <line x1="120" y1="95" x2="250" y2="100" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead)"/>
  <line x1="350" y1="100" x2="480" y2="95" stroke="#64748b" stroke-width="2" marker-end="url(#arrowhead)"/>
</svg>'''
    
    flow_path.write_text(svg_content)
    print(f"  ✅ Generated flow diagram: {flow_path}")
    return flow_path


def generate_html_preview(pack_dir: Path, pack_json: dict[str, Any]) -> Path:
    """Generate HTML preview from notebook."""
    assets_dir = pack_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    preview_path = assets_dir / "preview.html"
    entrypoint = pack_json.get("entrypoint", "main.ipynb")
    notebook_path = pack_dir / entrypoint
    
    if not notebook_path.exists():
        print(f"  ⚠️  Notebook not found: {entrypoint}")
        return preview_path
    
    # Try to convert notebook to HTML using nbconvert
    try:
        result = subprocess.run(
            ["jupyter", "nbconvert", "--to", "html", str(notebook_path), "--output", str(preview_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"  ✅ Generated HTML preview: {preview_path}")
        else:
            # Create a simple HTML placeholder
            html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>{pack_json.get("title", "Notebook Pack")} - Preview</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>{pack_json.get("title", "Notebook Pack")}</h1>
    <p><strong>Description:</strong> {pack_json.get("description", "")}</p>
    <p><strong>Category:</strong> {pack_json.get("category", "")}</p>
    <p><strong>Difficulty:</strong> {pack_json.get("difficulty", "")}</p>
    <p><strong>Runtime:</strong> {pack_json.get("runtime_minutes", 15)} minutes</p>
    <hr>
    <p><em>Full notebook preview requires jupyter nbconvert. Install with: pip install jupyter nbconvert</em></p>
</body>
</html>'''
            preview_path.write_text(html_content)
            print(f"  ⚠️  Created HTML placeholder (nbconvert failed): {preview_path}")
    except FileNotFoundError:
        # jupyter not found, create placeholder
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>{pack_json.get("title", "Notebook Pack")} - Preview</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>{pack_json.get("title", "Notebook Pack")}</h1>
    <p><strong>Description:</strong> {pack_json.get("description", "")}</p>
    <p><strong>Category:</strong> {pack_json.get("category", "")}</p>
    <p><strong>Difficulty:</strong> {pack_json.get("difficulty", "")}</p>
    <p><strong>Runtime:</strong> {pack_json.get("runtime_minutes", 15)} minutes</p>
    <hr>
    <p><em>Full notebook preview requires jupyter nbconvert. Install with: pip install jupyter nbconvert</em></p>
</body>
</html>'''
        preview_path.write_text(html_content)
        print(f"  ⚠️  Created HTML placeholder (jupyter not found): {preview_path}")
    except Exception as e:
        print(f"  ⚠️  Error generating HTML preview: {e}")
    
    return preview_path


def render_pack_previews(pack_id: str) -> bool:
    """Render previews for a single pack."""
    pack_dir = PACKS_DIR / pack_id
    
    if not pack_dir.exists():
        print(f"❌ Pack not found: {pack_id}")
        return False
    
    pack_json_path = pack_dir / "pack.json"
    if not pack_json_path.exists():
        print(f"❌ pack.json not found for {pack_id}")
        return False
    
    with open(pack_json_path) as f:
        pack_json = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"🎨 Rendering Previews: {pack_id}")
    print(f"{'='*70}")
    print(f"Title: {pack_json.get('title', pack_id)}")
    print()
    
    # Generate cover image
    print("1️⃣  Generating cover image...")
    generate_cover_image(pack_dir, pack_json)
    
    # Generate flow diagram
    print("\n2️⃣  Generating flow diagram...")
    generate_flow_diagram(pack_dir, pack_json)
    
    # Generate HTML preview
    print("\n3️⃣  Generating HTML preview...")
    generate_html_preview(pack_dir, pack_json)
    
    print(f"\n✅ Previews rendered for {pack_id}")
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Render previews for packs")
    parser.add_argument("pack_id", nargs="?", help="Pack ID to render (e.g., pack_0001). If not provided, renders all packs.")
    parser.add_argument("--all", action="store_true", help="Render all packs")
    
    args = parser.parse_args()
    
    if args.all or not args.pack_id:
        # Render all packs
        packs = sorted([d.name for d in PACKS_DIR.iterdir() if d.is_dir() and d.name.startswith("pack_")])
        if not packs:
            print("No packs found")
            return
        
        for pack_id in packs:
            render_pack_previews(pack_id)
    else:
        render_pack_previews(args.pack_id)


if __name__ == "__main__":
    main()
