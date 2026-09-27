"""Samson's separate page in the current private Savior deployment."""

from pathlib import Path
from runpy import run_path

# Execute on every Streamlit rerun; a regular import would only run once.
run_path(str(Path(__file__).resolve().parents[1] / "samson_app.py"))
