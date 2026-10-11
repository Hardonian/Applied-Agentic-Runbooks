import json
import sys

with open("Agentic_Notebook.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
for i, cell in enumerate(nb['cells']):
    ct = cell['cell_type']
    first = cell['source'][0].strip() if cell['source'] else ''
    # remove non-ascii for safe printing
    first_ascii = first.encode('ascii', errors='replace').decode('ascii')
    total_lines = len(cell['source'])
    print(f"{i:2d} | {ct:8s} | {total_lines:3d} lines | {first_ascii[:60]}")
