"""Resource ownership compatibility for the pinned pyelectroluxocp 0.1.3 SDK."""

import asyncio
from typing import Any

from pyelectroluxocp import OneAppApi


class _EntryTasks(set[asyncio.Task[Any]]):
    """Cancel SDK callback work immediately once its client starts closing."""

    def __init__(self) -> None:
        super().__init__()
        self.closed = False

    def add(self, task: asyncio.Task[Any]) -> None:
        super().add(task)
        if self.closed:
            task.cancel()


class ManagedOneAppApi(OneAppApi):
    """Isolate and drain tasks without changing SDK HTTP-session ownership."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # SDK 0.1.3 declares this mutable set on the class. Its public close()
        # would otherwise cancel every account's websocket and refresh tasks.
        # Keep this compatibility field until the pinned SDK is replaced.
        self._running_tasks = _EntryTasks()
        self._close_lock = asyncio.Lock()
        self._closed = False

    def begin_shutdown(self) -> None:
        """Prevent disconnect callbacks starting requests while the watch stops."""
        self._running_tasks.closed = True

    async def close(self) -> None:
        """Close vendor resources once and await this client's own tasks."""
        async with self._close_lock:
            if self._closed:
                return
            self.begin_shutdown()
            try:
                await super().close()
            finally:
                tasks = tuple(
                    task
                    for task in self._running_tasks
                    if task is not asyncio.current_task()
                )
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
            self._closed = True
