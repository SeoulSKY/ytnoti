"""Contains fixtures and utility functions."""

import os
import time
from datetime import UTC, datetime
from threading import Thread

import pytest
from dotenv import load_dotenv
from pyngrok import ngrok

from ytnoti import Channel, Timestamp, Video, YouTubeNotifier

CALLBACK_URL = "http://localhost:8000"

load_dotenv()
ngrok.set_auth_token(os.getenv("NGROK_TOKEN"))


@pytest.fixture(scope="session")
def notifier() -> YouTubeNotifier:
    """Setup/Teardown code that runs before and after the tests in this package."""
    noti = YouTubeNotifier()
    noti._config.password = ""
    thread = Thread(target=noti.run, name="notifier", daemon=True)
    thread.start()

    while True:
        if noti.is_ready:
            break

        time.sleep(0.1)

    yield noti

    noti.stop()


def get_channel() -> Channel:
    """Create a mock channel."""
    return Channel(
        id="mock_channel_id",
        name="Mock Channel",
        url="https://www.youtube.com/channel/mock_channel")

def get_video() -> Video:
    """Create a mock video."""
    return Video(
        id="mock_video_id",
        title="Mock Video",
        url="https://www.youtube.com/watch?v=mock_video",
        timestamp=Timestamp(
            published=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
            updated=datetime(2023, 1, 1, 13, 0, 0, tzinfo=UTC)
        ),
        channel=get_channel()
    )
