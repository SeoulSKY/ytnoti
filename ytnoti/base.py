"""
This module contains abstract base classes for the library.
"""

from abc import ABC, abstractmethod
import asyncio
import logging
import random
import string
from datetime import datetime
from http import HTTPStatus
from threading import Thread
from typing import Self, Literal, Iterable, Any, Callable
import hmac
from urllib.parse import urlparse

from httpx import AsyncClient
import xmltodict
from fastapi import FastAPI, Request, Response, APIRouter
from uvicorn import Config, Server
from pyngrok import ngrok
from pyexpat import ExpatError

from ytnoti.enums import NotificationKind, ServerMode
from ytnoti.errors import HTTPError
from ytnoti.models import YouTubeNotifierConfig
from ytnoti.models.history import InMemoryVideoHistory, VideoHistory
from ytnoti.models.video import Channel, Thumbnail, Video, Stats, Timestamp
from ytnoti.types import NotificationListener


class BaseYouTubeNotifier(ABC):
    """
    An abstract class for all YouTubeNotifier classes.
    """

    _ALL_LISTENER_KEY = "_all"

    def __init__(self,
                 logger: logging.Logger,
                 *,
                 callback_url: str = None,
                 password: str = None,
                 video_history: VideoHistory = None) -> None:
        """
        Set up the YouTubeNotifier instance.

        :param logger: The logger to use for logging.
        :param callback_url: The URL to receive push notifications. If not provided, ngrok will be used to create a
                             temporary URL.
        :param password: The password to use for verifying push notifications. If not provided, a random password will
                         be generated.
        :param video_history: The video history to use to prevent duplicate notifications. If not provided, a new
                              instance of InMemoryVideoHistory will be created and used.
        """

        self.__logger = logger
        self._config = YouTubeNotifierConfig(
            callback_url,
            "0.0.0.0",
            8000,
            FastAPI(),
            callback_url is None,
            password or str("".join(random.choice(string.ascii_letters) for _ in range(20))),
        )
        self._listeners: dict[NotificationKind, dict[str, list[NotificationListener]]] = \
            {kind: {} for kind in NotificationKind}
        self._server = None
        self._subscribed_ids: set[str] = set()
        self._video_history = video_history or InMemoryVideoHistory()
        self._server: Server | None = None

    @staticmethod
    @abstractmethod
    def _get_server_mode() -> ServerMode:
        """
        Get the server mode to run the server in.

        :return: The server mode.
        """

    @property
    def callback_url(self) -> str | None:
        """
        Get the callback URL. If the callback URL was not provided when creating the instance, it will become available
        after the notifier is started.

        :return: The callback URL.
        """

        return self._config.callback_url

    @property
    def is_ready(self) -> bool:
        """
        Check if the notifier is ready to receive push notifications.

        :return: True if the notifier is ready, False otherwise.
        """
        return self._server is not None

    def listener(self, *, kind: NotificationKind, channel_ids: str | Iterable[str] = None) \
            -> Callable[[NotificationListener], NotificationListener]:
        """
        A decorator to add a listener for push notifications.

        :param kind: The kind of notification to listen for.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        :raises ValueError: If the channel ID is '_all'.
        """

        def decorator(func: NotificationListener) -> NotificationListener:
            self.add_listener(func, kind, channel_ids)

            return func

        return decorator

    def any(self, *, channel_ids: str | Iterable[str] = None) \
            -> Callable[[NotificationListener], NotificationListener]:
        """
        A decorator to add a listener for any kind of push notification.
        Alias for @listener(kind=NotificationKind.ANY).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """

        return self.listener(kind=NotificationKind.ANY, channel_ids=channel_ids)

    def upload(self, *, channel_ids: str | Iterable[str] = None) \
            -> Callable[[NotificationListener], NotificationListener]:
        """
        A decorator to add a listener for when a video is uploaded.
        Alies for @listener(kind=NotificationKind.UPLOAD).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """

        return self.listener(kind=NotificationKind.UPLOAD, channel_ids=channel_ids)

    def edit(self, *, channel_ids: str | Iterable[str] = None) \
            -> Callable[[NotificationListener], NotificationListener]:
        """
        A decorator to add a listener for when a video is edited.
        Alies for @listener(kind=NotificationKind.EDIT).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """

        return self.listener(kind=NotificationKind.EDIT, channel_ids=channel_ids)

    def add_listener(self,
                     func: NotificationListener,
                     kind: NotificationKind,
                     channel_ids: str | Iterable[str] = None) -> Self:
        """
        Add a listener for push notifications.

        :param func: The listener function to add.
        :param kind: The kind of notification to listen for.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        :raises ValueError: If the channel ID is '_all'.
        """

        if channel_ids is None:
            self._get_listeners(kind, None).append(func)
            self.__logger.debug("Added %s listener (%s) for all channels", kind.name, func.__name__)
            return self

        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]

        for channel_id in channel_ids:
            if channel_id == self._ALL_LISTENER_KEY:
                raise ValueError(f"Channel ID cannot be '{self._ALL_LISTENER_KEY}'")

            self._get_listeners(kind, channel_id).append(func)
            self.__logger.debug("Added %s listener (%s) for channel: %s", kind.name, func.__name__, channel_id)

        return self

    def add_any_listener(self, func: NotificationListener, channel_ids: str | Iterable[str] = None) -> Self:
        """
        Add a listener for any kind of push notification.
        Alias for add_listener(func, NotificationKind.ANY, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        return self.add_listener(func, NotificationKind.ANY, channel_ids)

    def add_upload_listener(self, func: NotificationListener, channel_ids: str | Iterable[str] = None) -> Self:
        """
        Add a listener for when a video is uploaded.
        Alias for add_listener(func, NotificationKind.UPLOAD, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        return self.add_listener(func, NotificationKind.UPLOAD, channel_ids)

    def add_edit_listener(self, func: NotificationListener, channel_ids: str | Iterable[str] = None) -> Self:
        """
        Add a listener for when a video is edited.
        Alias for add_listener(func, NotificationKind.EDIT, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        return self.add_listener(func, NotificationKind.EDIT, channel_ids)

    async def _get_kind(self, video: Video) -> NotificationKind:
        """
        Get the kind of notification based on the video.

        :param video: The video to get the kind of notification for.
        :return: The kind of notification.
        """

        if video.timestamp.updated == video.timestamp.published:
            return NotificationKind.UPLOAD

        return NotificationKind.EDIT if await self._video_history.has(video) else NotificationKind.UPLOAD

    def _get_listeners(self, kind: NotificationKind, channel_id: str | None) -> list[NotificationListener]:
        """
        Get the listeners for the given kind and channel ID.

        :param kind: The kind of notification.
        :param channel_id: The channel ID to get the listeners for. If not provided, the listeners for all channels
        :return: The listeners for the given kind and channel ID.
        """

        key = channel_id or self._ALL_LISTENER_KEY
        listeners = self._listeners[kind].get(key, None)
        if listeners is None:
            listeners = []
            self._listeners[kind][key] = listeners

        return listeners

    def _get_router(self) -> APIRouter:
        """
        Get the FastAPI router for the notifier.

        :return: The FastAPI router.
        """

        router = APIRouter()
        endpoint = urlparse(self._config.callback_url).path or "/"
        router.add_api_route(endpoint, self._get, methods=["HEAD", "GET"])
        router.add_api_route(endpoint, self._post, methods=["POST"])

        return router

    def _get_server_config(self, **kwargs) -> Config:
        """
        Get the server configuration.

        :param kwargs: Additional arguments to pass to the server configuration.
        :return: The server configuration.
        """

        return Config(self._config.app, self._config.host, self._config.port, **kwargs)

    def _get_server(self,
                    *,
                    host: str,
                    port: int,
                    app: FastAPI = None,
                    **kwargs: Any) -> Server:
        """
        Create a server instance to receive push notifications.

        :param host: The host to run the server on.
        :param port: The port to run the server on.
        :param app: The FastAPI app to use. If not provided, a new app will be created.
        :param log_level: The log level to use for the uvicorn server.
        :param kwargs: Additional arguments to pass to the server configuration.
        :return: The server instance.
        """

        self._config.host = host
        self._config.port = port
        self._config.app = app or self._config.app

        if self._config.using_ngrok:
            self._config.callback_url = ngrok.connect(str(port)).public_url

        self.__logger.info("Callback URL: %s", self._config.callback_url)

        self._config.app.include_router(self._get_router())

        async def on_ready():
            while not await self._is_listening():
                await asyncio.sleep(0.1)

            self._server = server

            await self._register(self._subscribed_ids)

        async def repeat_subscribe(interval: float):
            while True:
                await asyncio.sleep(interval)
                await self._register(self._subscribed_ids)

        self._config.app.add_event_handler("startup", lambda: asyncio.create_task(on_ready()))
        self._config.app.add_event_handler("startup",
                                           lambda: asyncio.create_task(repeat_subscribe(60 * 60 * 24)))

        server = Server(Config(self._config.app, self._config.host, self._config.port, **kwargs))
        return server

    async def _is_listening(self) -> bool:
        """
        Check if the server is listening for push notifications.

        :return: True if the server is listening, False otherwise.
        """

        try:
            async with AsyncClient() as client:
                response = await client.head(self._config.callback_url, params={"hub.challenge": "1"})
        except ConnectionError:
            return False

        return response.status_code == HTTPStatus.OK.value

    async def _subscribe(self, channel_ids: str | Iterable[str]) -> None:
        """
        Subscribe to YouTube channels to receive push notifications. This is lazy and will subscribe when the
        notifier is ready. If the notifier is already ready, it will subscribe immediately.

        :param channel_ids: The channel ID(s) to subscribe to.
        :raises ValueError: If the channel ID is invalid.
        :raises HTTPError: If failed to verify the channel ID or failed to subscribe due to an HTTP error.
        """

        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]

        if not self.is_ready:
            self._subscribed_ids.update(channel_ids)
            return

        not_subscribed = set(channel_ids).difference(self._subscribed_ids)
        await self._register(not_subscribed)

        self._subscribed_ids.update(not_subscribed)

    async def _register(self,
                        channel_ids: Iterable[str],
                        *,
                        mode: Literal["subscribe", "unsubscribe"] = "subscribe") -> None:
        """
        Subscribe or unsubscribe to YouTube channels to receive push notifications.
        """

        async with AsyncClient() as client:
            for channel_id in channel_ids:
                response = await client.head(f"https://www.youtube.com/channel/{channel_id}")

                if response.status_code != HTTPStatus.OK.value:
                    raise ValueError(f"Invalid channel ID: {channel_id}")

        for channel_id in channel_ids:
            async with AsyncClient() as client:
                self.__logger.debug("Sending %s request for channel: %s", mode, channel_id)

                response = await client.post(
                    "https://pubsubhubbub.appspot.com",
                    data={
                        "hub.mode": mode,
                        "hub.topic": f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                        "hub.callback": self._config.callback_url,
                        "hub.verify": "sync",
                        "hub.secret": self._config.password,
                        "hub.lease_seconds": "",
                        "hub.verify_token": ""
                    },
                    headers={"Content-type": "application/x-www-form-urlencoded"}
                )

            if response.status_code == HTTPStatus.CONFLICT.value and not await self._is_listening():
                raise ConnectionError(f"Cannot {mode} while the server is not listening")

            if response.status_code != HTTPStatus.NO_CONTENT.value:
                raise HTTPError(f"Failed to {mode} channel: {channel_id}", response.status_code)

            self.__logger.info("Successfully %sd channel: %s", mode, channel_id)

    async def _stop(self) -> None:
        """
        Request to gracefully stop the notifier. If the notifier is not running, this method will do nothing.
        """

        if not self.is_ready:
            return

        await self._clean_up(running_server=self._server)
        self._server = None

    async def _clean_up(self, *, running_server: Server | None) -> None:
        """
        Clean up the notifier.
        
        :param running_server: The running server instance, or None if the server is not running.
        """

        self.__logger.debug("Cleaning up the notifier")

        # ngrok is already stopped at this point, so we can't unsubscribe if we are using ngrok.
        # It might not be matter though because ngrok generates unique URL every time, and the old URL will be invalid.
        if self._config.using_ngrok:
            return

        app = FastAPI()
        app.include_router(self._get_router())

        if running_server is None:
            self.__logger.debug("Temporarily running the server to unsubscribe the YouTube channels")
            # Run the server again to unsubscribe
            running_server = Server(Config(app, self._config.host, self._config.port, log_level=logging.WARNING))
            if self._get_server_mode() == ServerMode.RUN:
                Thread(target=running_server.run).start()
            else:
                _ = asyncio.create_task(running_server.serve())

        while not await self._is_listening():
            await asyncio.sleep(0.1)

        await self._register(self._subscribed_ids, mode="unsubscribe")

        await running_server.shutdown()

    @staticmethod
    async def _get(request: Request):
        """
        Handle challenge from the Google pubsubhubbub server.
        """

        challenge = request.query_params.get("hub.challenge")
        if challenge is None:
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        return Response(challenge)

    async def _post(self, request: Request):
        """
        Handle push notifications from the Google pubsubhubbub server.
        """

        if not await self._is_authorized(request):
            return Response(status_code=HTTPStatus.UNAUTHORIZED.value)

        try:
            body = xmltodict.parse((await request.body()))
        except ExpatError:
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        self.__logger.debug("Received push notification: %s", body)

        try:
            # entry can be list of dict or just dict
            entries = body["feed"]["entry"] if isinstance(body["feed"]["entry"], list) else [body["feed"]["entry"]]

            for entry in entries:
                channel = Channel(
                    id=entry["yt:channelId"],
                    name=entry["author"]["name"],
                    url=entry["author"]["uri"],
                    created_at=datetime.strptime(body["feed"]["published"], "%Y-%m-%dT%H:%M:%S%z")
                )

                thumbnail = Thumbnail(
                    url=entry["media:group"]["media:thumbnail"]["@url"],
                    width=int(entry["media:group"]["media:thumbnail"]["@width"]),
                    height=int(entry["media:group"]["media:thumbnail"]["@height"]),
                )

                # Uploader can hide video stats
                stats = None
                if "media:community" in entry["media:group"]:
                    stats = Stats(
                        likes=int(entry["media:group"]["media:community"]["media:starRating"]["@count"]),
                        views=int(entry["media:group"]["media:community"]["media:statistics"]["@views"]),
                    )

                timestamp = Timestamp(
                    published=datetime.strptime(entry["published"], "%Y-%m-%dT%H:%M:%S%z"),
                    updated=datetime.strptime(entry["updated"], "%Y-%m-%dT%H:%M:%S%z")
                )

                video = Video(
                    id=entry["yt:videoId"],
                    title=entry["title"],
                    description=entry["media:group"]["media:description"] or "",
                    url=entry["link"]["@href"],
                    thumbnail=thumbnail,
                    stats=stats,
                    timestamp=timestamp,
                    channel=channel
                )

                kind = await self._get_kind(video)
                listeners = (self._get_listeners(kind, None) +
                             self._get_listeners(kind, channel.id) +
                             self._get_listeners(NotificationKind.ANY, None) +
                             self._get_listeners(NotificationKind.ANY, channel.id))

                for func in listeners:
                    await func(video)

                if kind == NotificationKind.UPLOAD:
                    await self._video_history.add(video)
        except (TypeError, KeyError, ValueError):
            self.__logger.exception("Failed to parse request body: %s", body)
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        return Response(status_code=HTTPStatus.NO_CONTENT.value)

    async def _is_authorized(self, request: Request) -> bool:
        x_hub_signature = request.headers.get("X-Hub-Signature")
        # Check if the header is missing or invalid
        if x_hub_signature is None or "=" not in x_hub_signature:
            return False

        algorithm, value = x_hub_signature.split("=")
        hash_obj = hmac.new(self._config.password.encode(), await request.body(), algorithm)
        return hmac.compare_digest(hash_obj.hexdigest(), value)
