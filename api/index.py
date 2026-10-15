"""
Vercel Serverless Function entrypoint for Agent Factory Research Assistant App.
"""

from pathlib import Path
import sys

# Ensure repository root is on sys.path so agent_factory and apps are importable
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from apps.research_assistant_app.main import app  # noqa: F401
