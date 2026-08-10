from fastapi import APIRouter

from .v1 import v1_routes

api_routes = APIRouter()
api_routes.include_router(v1_routes, prefix = '/v1')
