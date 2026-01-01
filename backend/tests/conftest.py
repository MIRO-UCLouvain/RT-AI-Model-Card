"""Shared pytest fixtures for backend tests.

Adds the backend root to sys.path so imports like ``from models.user import User``
resolve correctly when tests are run from the repo root or the backend/ directory.
"""

import sys
from pathlib import Path

# Ensure the backend package root is on the path regardless of how pytest
# is invoked (from repo root, from backend/, or via an IDE test runner).
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
