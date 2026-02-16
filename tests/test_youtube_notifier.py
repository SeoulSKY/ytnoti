"""Contains the tests for the class YouTubeNotifier."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from fastapi import FastAPI

from tests import CALLBACK_URL
from ytnoti import AsyncYouTubeNotifier, YouTubeNotifier

channel_ids = [
    "UCPF-oYb2-xN5FbCXy0167Gg",
    "UCuFFtHWoLl5fauMMD5Ww2jA",
    "UCupvZG-5ko_eiXAupbDfxWw",
]


@pytest.fixture
def notifier() -> YouTubeNotifier:
    """Fixture for YouTubeNotifier."""
    app = FastAPI()
    notifier = YouTubeNotifier(app=app, callback_url=CALLBACK_URL)
    notifier._password = ""

    notifier._set_app_routes(app=app, callback_url=CALLBACK_URL)

    return notifier


def test_run() -> None:
    """Test run method of the YouTubeNotifier class."""
    notifier = YouTubeNotifier(callback_url=CALLBACK_URL)

    with (
        patch("ytnoti.Server"),
        patch.object(notifier, "_on_exit") as mock_exit,
    ):
        notifier.run()
        mock_exit.assert_called_once()


def test_run_in_background() -> None:
    """Test run_in_background method of the YouTubeNotifier class."""
    notifier = YouTubeNotifier(callback_url=CALLBACK_URL)

    with notifier.run_in_background():
        assert notifier.is_ready


@pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
def test_run_in_background_error() -> None:
    """Test run_in_background method when the server thread dies unexpectedly."""
    notifier = YouTubeNotifier(callback_url=CALLBACK_URL)

    # Force is_ready to stay False so the loop continues until thread death
    with (
        patch.object(notifier, "run", side_effect=RuntimeError("Mock error")),
        patch.object(
            YouTubeNotifier, "is_ready", new_callable=PropertyMock
        ) as mock_is_ready,
    ):
        mock_is_ready.return_value = False
        with (
            pytest.raises(RuntimeError, match="Server thread died unexpectedly"),
            notifier.run_in_background(),
        ):
            pass


def test_subscribe(notifier: YouTubeNotifier) -> None:
    """Test subscribe method of the YouTubeNotifier class."""
    with patch.object(AsyncYouTubeNotifier, "subscribe") as mock_subscribe:
        notifier.subscribe(channel_ids)
        mock_subscribe.assert_awaited_with(channel_ids)


def test_unsubscribe(notifier: YouTubeNotifier) -> None:
    """Test unsubscribe method of the YouTubeNotifier class."""
    with patch.object(AsyncYouTubeNotifier, "unsubscribe") as mock_unsubscribe:
        notifier.unsubscribe(channel_ids)
        mock_unsubscribe.assert_awaited_with(channel_ids)


def test_run_coroutine() -> None:
    """Test _run_coroutine method of the YouTubeNotifier class."""
    called = 0

    async def test() -> None:
        nonlocal called
        called += 1

    YouTubeNotifier._run_coroutine(test())
    assert called == 1

    mock_loop = MagicMock()
    with patch("asyncio.get_running_loop", return_value=mock_loop):
        YouTubeNotifier._run_coroutine(test())
        mock_loop.run_until_complete.assert_called_once()
