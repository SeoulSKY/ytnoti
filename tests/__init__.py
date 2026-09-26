"""Contains fixtures and utility functions."""

import socket
from datetime import UTC, datetime

from ytnoti import Channel, Timestamp, Video

CALLBACK_URL = "http://localhost:8000"


def get_free_port() -> int:
    """Get a local port that nothing is listening on, so that a test starting a
    real server never collides with another server on a fixed port.
    """
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def get_channel() -> Channel:
    """Create a mock channel."""
    return Channel(
        id="mock_channel_id",
        name="Mock Channel",
        url="https://www.youtube.com/channel/mock_channel",
    )


def get_video() -> Video:
    """Create a mock video."""
    return Video(
        id="mock_video_id",
        title="Mock Video",
        url="https://www.youtube.com/watch?v=mock_video",
        timestamp=Timestamp(
            published=datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC),
            updated=datetime(2023, 1, 1, 13, 0, 0, tzinfo=UTC),
        ),
        channel=get_channel(),
    )
