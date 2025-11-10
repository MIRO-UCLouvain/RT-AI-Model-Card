"""API v1 router.

Routes are registered here as features are implemented.
Currently empty — the /health endpoint lives directly on the FastAPI app
in main.py so it is reachable without the /v1 prefix.
"""

from fastapi import APIRouter

api_v1_router = APIRouter(prefix="/v1")

# Phase 1 — examples:    from backend.api.v1.routes import examples
# Phase 2 — model cards: from backend.api.v1.routes import model_cards
# Phase 3 — compare:     from backend.api.v1.routes import compare
# Phase 4 — feedback:    from backend.api.v1.routes import feedback
