"""Test the FileVideoHistory class."""

import shutil
from collections.abc import Iterable
from pathlib import Path

import pytest

from tests import get_video
from ytnoti.models.history import FileVideoHistory

NUM_VIDEOS = 100


@pytest.fixture
def history() -> Iterable[FileVideoHistory]:
    """Create a FileVideoHistory instance."""
    path = Path("./history")
    path.mkdir(parents=True, exist_ok=True)

    yield FileVideoHistory(dir_path=path, num_videos=NUM_VIDEOS)

    shutil.rmtree(path)


@pytest.mark.asyncio
async def test_has(history: FileVideoHistory) -> None:
    """Test the has method of the FileVideoHistory class."""
    video = get_video()
    path = history._get_path(video.channel)

    assert not await history.has(video)

    with path.open("w") as file:
        file.write(video.id)

    assert await history.has(video)

    new_video = get_video()
    new_video.id = "-1"
    assert not await history.has(new_video)


@pytest.mark.asyncio
async def test_truncate(history: FileVideoHistory) -> None:
    """Test the truncate method of the FileVideoHistory class."""
    video = get_video()
    path = history._get_path(video.channel)

    # it should be no-op if the file does not exist
    await history._truncate(video.channel)

    with path.open("w") as file:
        for _ in range(NUM_VIDEOS + 5):
            file.write(video.id + "\n")

    await history._truncate(video.channel)

    with path.open("r") as file:
        lines = file.readlines()
        assert len(lines) == NUM_VIDEOS


@pytest.mark.asyncio
async def test_add(history: FileVideoHistory) -> None:
    """Test the add method of the FileVideoHistory class."""
    video = get_video()
    video.id = "-1"
    path = history._get_path(video.channel)

    await history.add(video)
    await history.add(video)

    with path.open("r") as file:
        assert file.readlines() == [f"{video.id}\n"]

    for i in range(NUM_VIDEOS):
        new_video = get_video()
        new_video.id = str(i)
        await history.add(new_video)

    # The oldest videos are evicted once the file is full, and adding the same
    # video over and over can no longer push the others out.
    with path.open("r") as file:
        lines = [line.strip() for line in file]

    assert len(lines) == NUM_VIDEOS
    assert video.id not in lines
    assert not await history.has(video)
    assert await history.has(new_video)
