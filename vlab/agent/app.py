import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

import vlab.agent.device as device

@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(device.main())

    yield

    task.cancel()
    await asyncio.gather(task, return_exceptions = True)

app = FastAPI(lifespan = lifespan)
