import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import cast

import vlab.agent.device as device

from .routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(device.main(cast(device.HasDynamicState, app)))

    yield

    task.cancel()
    await asyncio.gather(task, return_exceptions = True)

app = FastAPI(lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins = ['*'],
    allow_credentials = True,
    allow_methods = ['*'],
    allow_headers = ['*']
)

app.include_router(router)
