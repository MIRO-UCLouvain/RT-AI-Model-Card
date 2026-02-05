"""Shared pytest fixtures for backend tests.

Adds the backend root and repo root to sys.path so imports like
``from models.user import User`` and ``from app.services.markdown.renderer import …``
resolve correctly when tests are run from the repo root or the backend/ directory.
"""

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent   # TFG-Silvia/backend/
_REPO_ROOT = _BACKEND_ROOT.parent                        # TFG-Silvia/

for _p in (_BACKEND_ROOT, _REPO_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
