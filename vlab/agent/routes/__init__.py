from fastapi import FastAPI

from .api import api_routes

router = FastAPI()

router.include_router(api_routes, prefix = '/api')
