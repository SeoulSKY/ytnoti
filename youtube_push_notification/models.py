from dataclasses import dataclass
from datetime import datetime


@dataclass
class Channel:
    id: str
    name: str
    url: str


@dataclass
class Thumbnail:
    url: str
    width: int
    height: int


@dataclass
class VideoStats:
    likes: int
    views: int


@dataclass
class Video:
    id: str
    title: str
    description: str
    url: str
    thumbnail: Thumbnail
    stats: VideoStats | None
    timestamp: datetime


@dataclass
class PushNotification:
    channel: Channel
    video: Video
