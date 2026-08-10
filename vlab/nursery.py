import asyncio
from typing import Coroutine, Self

class Nursery:
    def __init__(self):
        self.__tasks: list[asyncio.Task] = []
    
        self.__task_start_monitor = asyncio.create_task(self.__start_monitor())

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_):
        await self.__task_start_monitor

    def create_task(self, coroutine: Coroutine) -> asyncio.Task:
        task = asyncio.create_task(coroutine)

        self.__tasks.append(task)

        return task

    async def __monitor(self):
        dones, pendings = await asyncio.wait(
            self.__tasks,
            return_when = asyncio.FIRST_COMPLETED
        )

        for task_done in dones:
            if (not task_done.cancelled()) and (exception := task_done.exception()):
                for task_pending in pendings:
                    task_pending.cancel()
                raise exception
            else:
                self.__tasks.remove(task_done)

    async def __start_monitor(self):
        while self.__tasks:
            await self.__monitor()

    def stop_all_tasks(self):
        for task in self.__tasks:
            task.cancel()
