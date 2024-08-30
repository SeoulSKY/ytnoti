from datetime import UTC, datetime

from ytnoti import Channel, Timestamp, Video


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
