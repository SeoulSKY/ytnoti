"""Contains the tests for the class AsyncYouTubeNotifier."""


import asyncio

import pytest

from ytnoti import AsyncYouTubeNotifier

tasks = set()


@pytest.mark.asyncio
async def test_run() -> None:
    """Test run method."""
    notifier = AsyncYouTubeNotifier()

    tasks.add(asyncio.create_task(notifier.run(port=8001)))
    await asyncio.sleep(2)
    assert notifier.is_ready


@pytest.mark.asyncio
async def test_run_in_background() -> None:
    """Test run_in_background method."""
    notifier = AsyncYouTubeNotifier()

    async with notifier.run_in_background(port=8002) as task:
        tasks.add(task)
        await asyncio.sleep(2)
        assert notifier.is_ready
