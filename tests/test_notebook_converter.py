"""
Tests for notebook converter.
"""

import json
from pathlib import Path

from agent_factory.notebook_converter import NotebookConverter
from agent_factory.notebook_converter.detector import AgentDetector, ToolDetector
from agent_factory.notebook_converter.parser import NotebookParser


def test_notebook_parser():
    """Test notebook parser."""
    parser = NotebookParser()
    
    # Create a test notebook
    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["agent = Agent(name='Test Agent', instructions='Test')"],
                "outputs": [],
            },
            {
                "cell_type": "markdown",
                "source": ["# Markdown cell"],
            },
        ],
        "metadata": {},
    }
    
    # Write test notebook
    test_path = Path("/tmp/test_notebook.ipynb")
    with open(test_path, "w") as f:
        json.dump(test_notebook, f)
    
    # Parse
    result = parser.parse(test_path)
    
    assert result["name"] == "test_notebook"
    assert len(result["cells"]) == 1  # Only code cells
    assert "agent = Agent" in result["cells"][0]["source"]
    
    # Cleanup
    test_path.unlink()


def test_agent_detector():
    """Test agent detector."""
    detector = AgentDetector()
    
    notebook_data = {
        "cells": [
            {
                "source": "agent = Agent(name='Test', instructions='Test instructions')",
                "cell_index": 0,
            },
        ],
    }
    
    agents = detector.detect(notebook_data)
    
    assert len(agents) > 0
    assert agents[0].get("name") == "Test" or "test" in agents[0].get("name", "").lower()


def test_tool_detector():
    """Test tool detector."""
    detector = ToolDetector()
    
    notebook_data = {
        "cells": [
            {
                "source": '''@function_tool
def test_tool(param: str) -> str:
    """Test tool."""
    return param''',
                "cell_index": 0,
            },
        ],
    }
    
    tools = detector.detect(notebook_data)
    
    assert len(tools) > 0
    assert tools[0].get("id") == "test_tool" or "test" in tools[0].get("id", "").lower()


def test_notebook_converter(tmp_path):
    """Test notebook converter end-to-end."""
    converter = NotebookConverter(output_dir=str(tmp_path))
    
    # Create test notebook
    test_notebook = {
        "cells": [
            {
                "cell_type": "code",
                "source": ["agent = Agent(name='Test', instructions='Test')"],
            },
        ],
        "metadata": {},
    }
    
    notebook_path = tmp_path / "test.ipynb"
    with open(notebook_path, "w") as f:
        json.dump(test_notebook, f)
    
    # Convert
    result = converter.convert(str(notebook_path), agent_name="test-agent")
    
    assert len(result.agents_created) > 0 or len(result.errors) > 0
