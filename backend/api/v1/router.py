"""API v1 router."""

from fastapi import APIRouter

from api.v1.routes.admin import router as admin_router
from api.v1.routes.auth import router as auth_router
from api.v1.routes.model_cards import router as model_cards_router
from api.v1.routes.public_cards import router as public_cards_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(model_cards_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(public_cards_router)
