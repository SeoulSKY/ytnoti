"""
This module contains the dataclasses used in the YouTubeNotifier

Classes:
    YouTubeNotifierConfig
"""


from dataclasses import dataclass


@dataclass
class YouTubeNotifierConfig:
    """
    Represents the configuration of the YouTubeNotifier
    """

    callback_url: str | None
    """The URL to receive notifications from YouTube"""

    password: str
    """The password to authenticate the YouTubeNotifier"""

    cache_size: int
    """The size of the cache for the YouTubeNotifier"""
