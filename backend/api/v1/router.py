"""API v1 router.

Routes are registered here as features are implemented.
Currently empty — the /health endpoint lives directly on the FastAPI app
in main.py so it is reachable without the /v1 prefix.
"""

from fastapi import APIRouter

from api.v1.routes.model_cards import router as model_cards_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(model_cards_router)

# Future routers (uncomment as implemented):
# Phase 1 — examples:  from api.v1.routes.examples import router as examples_router
# Phase 3 — compare:   from api.v1.routes.compare import router as compare_router
# Phase 4 — feedback:  from api.v1.routes.feedback import router as feedback_router
