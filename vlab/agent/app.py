import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
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

app.include_router(router)
