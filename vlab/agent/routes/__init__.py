from fastapi import APIRouter

from .api import api_routes

router = APIRouter()

router.include_router(api_routes, prefix = '/api')
