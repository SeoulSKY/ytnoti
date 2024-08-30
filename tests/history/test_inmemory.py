"""Test class InMemoryFileHistory."""

import pytest

from tests import get_video
from ytnoti import NotificationKind, YouTubeNotifier
from ytnoti.models.history import InMemoryVideoHistory

CACHE_SIZE = 100

@pytest.fixture
def history() -> InMemoryVideoHistory:
    """Create a mock FileVideoHistory instance."""
    return InMemoryVideoHistory(cache_size=CACHE_SIZE)


def test_cache_size(history: InMemoryVideoHistory) -> None:
    """Test the cache size of the InMemoryVideoHistory class."""
    assert history.cache_size == CACHE_SIZE
    history.cache_size = 1
    assert history.cache_size == 1


@pytest.mark.asyncio
async def test_has(history: InMemoryVideoHistory) -> None:
    """Test the has method of the InMemoryVideoHistory class."""
    video = get_video()

    assert not await history.has(video)

    history._video_ids[video.id] = None

    assert await history.has(video)

@pytest.mark.asyncio
async def test_add(history: InMemoryVideoHistory) -> None:
    """Test the add method of the InMemoryVideoHistory class."""
    video = get_video()
    video.id = "-1"

    await history.add(video)
    await history.add(video)
    assert len(history._video_ids) == 1

    assert video.id in history._video_ids

    for i in range(CACHE_SIZE + 1):
        new_video = get_video()
        new_video.id = str(i)
        await history.add(new_video)

    assert len(history._video_ids) == CACHE_SIZE
    assert video.id not in history._video_ids


@pytest.mark.asyncio
async def test_get_kind() -> None:
    """Test getting the kind."""
    notifier = YouTubeNotifier()
    video = get_video()
    video.timestamp.published = video.timestamp.updated

    assert await notifier._get_kind(video) == NotificationKind.UPLOAD

    await notifier._video_history.add(video)
    assert await notifier._get_kind(video) == NotificationKind.UPLOAD
