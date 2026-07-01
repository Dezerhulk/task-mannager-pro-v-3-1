"""Compatibility shim for the canonical FastAPI application.

The production implementation now lives in the nested project tree under
``task_manager/task manager pro``. This root-level module re-exports the
canonical app so legacy tooling keeps working during the migration.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent / "task_manager" / "task manager pro"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.main_pro import app  # noqa: E402,F401

__all__ = ["app"]
