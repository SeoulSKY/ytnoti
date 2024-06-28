"""
This module contains the dataclasses used in the YouTubeNotifier

Classes:
    YouTubeNotifierConfig
"""


from dataclasses import dataclass

from fastapi import FastAPI


@dataclass
class YouTubeNotifierConfig:
    """
    Represents the configuration of the YouTubeNotifier
    """

    callback_url: str | None
    """The URL to receive notifications from YouTube"""

    endpoint: str
    """The endpoint to receive notifications from YouTube"""

    port: int
    """The port to receive notifications from YouTube"""

    app: FastAPI
    """The FastAPI app to receive notifications from YouTube"""

    using_ngrok: bool
    """Whether to use ngrok to receive notifications from YouTube"""

    password: str
    """The password to authenticate the YouTubeNotifier"""

    cache_size: int
    """The size of the cache for the YouTubeNotifier"""
