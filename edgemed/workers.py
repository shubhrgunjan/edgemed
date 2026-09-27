"""Cooperative shutdown: wait for to_thread work before closing shared native handles."""

import asyncio


async def repeat(stop, function, on_error=None):
    while not stop.is_set():
        try:
            result = await asyncio.to_thread(function)
        except Exception:
            result = None
            if on_error:
                on_error()
        try:
            await asyncio.wait_for(stop.wait(), timeout=0.05 if result else 1)
        except TimeoutError:
            pass


async def finish(stop, tasks):
    stop.set()
    done, pending = await asyncio.wait(tasks, timeout=120)
    if pending:
        # Do not cancel native work or close resources underneath it.
        raise RuntimeError("Workers are still active; storage remains open")
    for task in done:
        task.result()
