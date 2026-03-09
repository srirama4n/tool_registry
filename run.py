#!/usr/bin/env python3
"""Run the Tool Registry app. Use: python run.py (or ./run.sh for bash)"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

# Build UI if dist doesn't exist
ui_dir = ROOT / "tool-registry-ui"
dist_dir = ui_dir / "dist"
if not dist_dir.exists() and ui_dir.exists():
    print("Building UI...")
    if subprocess.run(["npm", "run", "build"], cwd=ui_dir, capture_output=True).returncode != 0:
        print("UI build skipped (npm run build failed)")

# Run uvicorn
venv_uvicorn = ROOT / ".venv" / "bin" / "uvicorn"
if not venv_uvicorn.exists():
    print("Error: .venv not found. Run: python -m venv .venv && pip install -r requirements.txt")
    sys.exit(1)
os.execv(str(venv_uvicorn), ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
