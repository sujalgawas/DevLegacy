from fastAPI import APIRouter
from api.endpoints import User

api_router = APIRouter()

api_router.include_router(User.router, prefix="/user", tags=["user"])