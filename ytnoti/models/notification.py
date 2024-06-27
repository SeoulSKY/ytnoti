"""
This module contains the dataclasses for the notification model.

Classes:
    Channel
    Thumbnail
    Stats
    Timestamp
    Video
    Notification
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Channel:
    """
    Represents a YouTube channel
    """

    id: str
    """The unique ID of the channel"""

    name: str
    """The name of the channel"""

    url: str
    """The URL of the channel"""

    created_at: datetime
    """The time when the channel was created"""


@dataclass
class Thumbnail:
    """
    Represents a thumbnail of a video
    """

    url: str
    """The URL of the thumbnail"""

    width: int
    """The width of the thumbnail"""

    height: int
    """The height of the thumbnail"""


@dataclass
class Stats:
    """
    Represents the stats of a video
    """

    likes: int
    """The number of likes of the video"""

    views: int
    """The number of views of the video"""


@dataclass
class Timestamp:
    """
    Represents the timestamps of a video
    """

    published: datetime
    """The published time of the video"""

    updated: datetime
    """The updated time of the video"""


@dataclass
class Video:
    """
    Represents a YouTube video
    """

    id: str
    """The unique ID of the video"""

    title: str
    """The title of the video"""

    description: str
    """The description of the video"""

    url: str
    """The URL of the video"""

    thumbnail: Thumbnail
    """The thumbnail of the video"""

    stats: Stats | None
    """The stats of the video, if available"""

    timestamp: Timestamp
    """The timestamps of the video"""


@dataclass
class Notification:
    """
    Represents a notification
    """

    channel: Channel
    """The channel of the notification"""

    video: Video
    """The video of the notification"""
