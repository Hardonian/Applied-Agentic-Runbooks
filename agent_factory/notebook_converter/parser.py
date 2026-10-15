"""
Parse Jupyter notebook files.
"""

import json
from pathlib import Path
from typing import Any


class NotebookParser:
    """Parse .ipynb files and extract code cells."""
    
    def parse(self, notebook_path: Path) -> dict[str, Any]:
        """
        Parse a notebook file.
        
        Args:
            notebook_path: Path to .ipynb file
        
        Returns:
            Parsed notebook data with cells and metadata
        """
        with open(notebook_path, "r", encoding="utf-8") as f:
            notebook_json = json.load(f)
        
        # Extract code cells
        code_cells = []
        for cell in notebook_json.get("cells", []):
            if cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                code_cells.append({
                    "source": source,
                    "cell_index": len(code_cells),
                    "outputs": cell.get("outputs", []),
                })
        
        return {
            "path": str(notebook_path),
            "name": notebook_path.stem,
            "cells": code_cells,
            "metadata": notebook_json.get("metadata", {}),
        }
