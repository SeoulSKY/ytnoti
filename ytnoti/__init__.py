"""
This module defines the YouTubePushNotifier class which is used to subscribe to YouTube channels and receive push
notifications when new videos are uploaded or old videos are updated.
"""

import asyncio
import logging
import signal
from typing import Self, Iterable, Any, Coroutine

from fastapi import FastAPI

from ytnoti.base import BaseYouTubeNotifier
from ytnoti.enums import NotificationKind, ServerMode
from ytnoti.models import YouTubeNotifierConfig
from ytnoti.models.history import VideoHistory
from ytnoti.models.video import Channel, Thumbnail, Video, Stats, Timestamp
from ytnoti.types import NotificationListener, T


class YouTubeNotifier(BaseYouTubeNotifier):
    """
    A class that encapsulates the functionality for subscribing to YouTube channels and receiving push notifications.
    """

    def __init__(self,
                 *,
                 callback_url: str = None,
                 password: str = None,
                 video_history: VideoHistory = None) -> None:
        """
        Create a new YouTubeNotifier instance.

        :param callback_url: The URL to receive push notifications. If not provided, ngrok will be used to create a
                             temporary URL.
        :param password: The password to use for verifying push notifications. If not provided, a random password will
                         be generated.
        :param video_history: The video history to use to prevent duplicate notifications. If not provided, a new
                              instance of InMemoryVideoHistory will be created and used.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        super().__init__(
            self._logger,
            callback_url=callback_url,
            password=password,
            video_history=video_history
        )

    @staticmethod
    def _get_server_mode() -> ServerMode:
        return ServerMode.RUN

    def subscribe(self, channel_ids: str | Iterable[str]) -> Self:
        """
        Subscribe to YouTube channels to receive push notifications. This is lazy and will subscribe when the
        notifier is ready. If the notifier is already ready, it will subscribe immediately.

        :param channel_ids: The channel ID(s) to subscribe to.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        self._run_coroutine(super()._subscribe(channel_ids))

        return self

    def run(self,
            *,
            host: str = "0.0.0.0",
            port: int = 8000,
            app: FastAPI = None,
            log_level: int = logging.WARNING,
            **kwargs: Any) -> None:
        """
        Run the notifier to receive push notifications. This method will block until the notifier is stopped.

        :param host: The host to run the server on.
        :param port: The port to run the server on.
        :param app: The FastAPI app to use. If not provided, a new app will be created.
        :param log_level: The log level to use for the uvicorn server.
        :param kwargs: Additional arguments to pass to the Config class of uvicorn.
        """

        server = super()._get_server(host=host, port=port, app=app, log_level=log_level, **kwargs)

        try:
            server.run()
        except KeyboardInterrupt:
            # KeyboardInterrupt occurs if run() is running in main thread.
            # In this case, the server automatically stops, so we indicate here that the server is gone
            self._run_coroutine(super()._clean_up(running_server=None))
        else:
            self.stop()

    def stop(self) -> None:
        """
        Request to gracefully stop the notifier. If the notifier is not running, this method will do nothing.
        This method will block until the notifier is stopped.
        """

        if self._server is None:
            return

        self._run_coroutine(super()._stop())

    @staticmethod
    def _run_coroutine(coro: Coroutine[Any, Any, T]) -> T:
        """
        Run a coroutine in the event loop.

        :param coro: The coroutine to run.
        :return: The result of the coroutine.
        """

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        return loop.run_until_complete(coro)


class AsyncYouTubeNotifier(BaseYouTubeNotifier):
    """
    Asynchronous version of the YouTubeNotifier class.
    """

    def __init__(self,
                 *,
                 callback_url: str = None,
                 password: str = None,
                 video_history: VideoHistory = None) -> None:
        """
        Create a new AsyncYouTubeNotifier instance.

        :param callback_url: The URL to receive push notifications. If not provided, ngrok will be used to create a
                             temporary URL.
        :param password: The password to use for verifying push notifications. If not provided, a random password will
                         be generated.
        :param video_history: The video history to use to prevent duplicate notifications. If not provided, a new
                              instance of InMemoryVideoHistory will be created and used.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        super().__init__(
            self._logger,
            callback_url=callback_url,
            password=password,
            video_history=video_history
        )

    @staticmethod
    def _get_server_mode() -> ServerMode:
        return ServerMode.SERVE

    async def subscribe(self, channel_ids: str | Iterable[str]) -> None:
        """
        Subscribe to YouTube channels to receive push notifications. This is lazy and will subscribe when the
        notifier is ready. If the notifier is already ready, it will subscribe immediately.

        :param channel_ids: The channel ID(s) to subscribe to.
        """
        await super()._subscribe(channel_ids)

    async def serve(self,
                    *,
                    host: str = "0.0.0.0",
                    port: int = 8000,
                    log_level: int = logging.WARNING,
                    app: FastAPI = None,
                    **kwargs: Any) -> None:
        """
        Start the FastAPI server to receive push notifications in an existing event loop.

        :param host: The host to run the FastAPI server on.
        :param port: The port to run the FastAPI server on.
        :param log_level: The log level to use for the uvicorn server.
        :param app: The FastAPI app instance to use. If not provided, a new instance will be created.
        :param kwargs: Additional arguments to pass to the Config class of uvicorn.

        :raises RuntimeError: If the method is not called from a running event loop.
        """

        try:
            _ = asyncio.get_running_loop()
        except RuntimeError as ex:
            raise RuntimeError("serve() must be called from a running event loop") from ex

        server = super()._get_server(host=host, port=port, app=app, log_level=log_level, **kwargs)

        old_signal_handler = signal.getsignal(signal.SIGINT)

        async def signal_handler():
            await self._clean_up(running_server=None)

            signal.signal(signal.SIGINT, old_signal_handler)
            signal.raise_signal(signal.SIGINT)

        signal.signal(signal.SIGINT, lambda sig, frame: asyncio.create_task(signal_handler()))

        try:
            await server.serve()
        except KeyboardInterrupt:
            await self.stop()

    async def stop(self) -> None:
        """
        Request to gracefully stop the notifier. If the notifier is not running, this method will do nothing.
        """

        await super()._stop()
