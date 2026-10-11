import json
import traceback
import sys
import io

# Set stdout to UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open("Agentic_Notebook.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

scope = {}

print("Testing execution of code cells in Agentic_Notebook.ipynb...")
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    code = "".join(cell["source"])
    if i in (2, 6):
        print(f"Skipping cell {i:2d} (setup/interactive)")
        continue
    print(f"\n--- Running cell {i:2d} ---")
    try:
        exec(code, scope)
        print(f"Cell {i:2d} OK!")
    except Exception as e:
        print(f"Cell {i:2d} FAILED with {e}")
        traceback.print_exc()
        break

print("\nFinished testing all code cells.")
