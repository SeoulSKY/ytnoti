"""
This module defines the YouTubePushNotifier class which is used to subscribe to YouTube channels and receive push
notifications when new videos are uploaded or old videos are updated.

The YouTubeNotifier class provides methods to add listeners for specific channels or all channels, subscribe to
channels, and run the notifier.

Classes:
    YouTubeNotifier: A class that encapsulates the functionality for subscribing to YouTube channels and
    receiving push notifications.
"""

import asyncio
import logging
from typing import Self, Iterable, Any

from fastapi import FastAPI

from ytnoti.base import BaseYouTubeNotifier
from ytnoti.enums import NotificationKind
from ytnoti.models import YouTubeNotifierConfig
from ytnoti.models.notification import Notification, Channel, Thumbnail, Video, Stats, Timestamp
from ytnoti.types import PushNotificationListener, ReadyListener


class YouTubeNotifier(BaseYouTubeNotifier):
    """
    A class that encapsulates the functionality for subscribing to YouTube channels and receiving push notifications.
    """

    def __init__(self,
                 *,
                 callback_url: str = None,
                 password: str = None,
                 cache_size: int = 5000) -> None:
        """
        Create a new YouTubeNotifier instance.

        :param callback_url: The URL to receive push notifications. If not provided, ngrok will be used to create a
                             temporary URL.
        :param password: The password to use for verifying push notifications. If not provided, a random password will
                         be generated.
        :param cache_size: The number of video IDs to keep in the cache to prevent duplicate notifications.
        """

        super().__init__(callback_url=callback_url, password=password, cache_size=cache_size)

        self._logger = logging.getLogger(self.__class__.__name__)

    def subscribe(self, channel_ids: str | Iterable[str]) -> Self:
        """
        Subscribe to YouTube channels to receive push notifications. This is lazy and will subscribe when the
        notifier is ready. If the notifier is already ready, it will subscribe immediately.

        :param channel_ids: The channel ID(s) to subscribe to.
        :return: The YouTubeNotifier instance to allow for method chaining.
        :raises ValueError: If the channel ID is invalid.
        :raises HTTPError: If failed to verify the channel ID or failed to subscribe due to an HTTP error.
        """

        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]

        if not self.is_ready:
            self._subscribed_ids.update(channel_ids)
            return self

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        not_subscribed = set(channel_ids).difference(self._subscribed_ids)
        loop.run_until_complete(self._subscribe(not_subscribed))
        self._subscribed_ids.update(channel_ids)

        return self

    def run(self,
            *,
            endpoint: str = "/",
            port: int = 8000,
            app: FastAPI = None,
            log_level: int = logging.WARNING,
            **kwargs: Any) -> None:
        """
        Run the notifier to receive push notifications. This method will block until the notifier is stopped.

        :param endpoint: The endpoint to receive push notifications.
        :param port: The port to run the server on.
        :param app: The FastAPI app to use. If not provided, a new app will be created.
        :param log_level: The log level to use for the uvicorn server.
        :param kwargs: Additional arguments to pass to the server configuration.
        """

        server = self._setup(endpoint=endpoint, port=port, app=app, log_level=log_level, **kwargs)

        try:
            server.run()
        except KeyboardInterrupt:
            # KeyboardInterrupt occurs if run() is running in main thread.
            # In this case, the server automatically stops, so we indicate here that the server is gone
            asyncio.run(self._clean_up(None))
        else:
            self.stop()

    def stop(self) -> None:
        """
        Request to gracefully stop the notifier. If the notifier is not running, this method will do nothing.
        This method will block until the notifier is stopped.
        """

        if self._server is None:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        loop.run_until_complete(self._clean_up(self._server))
