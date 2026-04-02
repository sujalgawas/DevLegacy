from fastapi import APIRouter
from app.api.endpoints import User, analysis

api_router = APIRouter()

api_router.include_router(User.router, prefix="/user", tags=["user"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])