"""Contains the dataclasses for the video model."""

__all__ = ["Video", "Channel", "Timestamp"]


from dataclasses import dataclass
from datetime import datetime


@dataclass
class Channel:
    """Represents a YouTube channel."""

    id: str
    """The unique ID of the channel"""

    name: str
    """The name of the channel"""

    url: str
    """The URL of the channel"""


@dataclass
class Timestamp:
    """Represents the timestamps of a video."""

    published: datetime
    """The published time of the video"""

    updated: datetime
    """The updated time of the video"""


@dataclass
class Video:
    """Represents a YouTube video."""

    id: str
    """The unique ID of the video"""

    title: str
    """The title of the video"""

    url: str
    """The URL of the video"""

    timestamp: Timestamp
    """The timestamps of the video"""

    channel: Channel
    """The channel of the video"""
