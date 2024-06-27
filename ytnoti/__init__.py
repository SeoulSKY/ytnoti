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
import random
import signal
import string
from collections import OrderedDict
from datetime import datetime
from http import HTTPStatus
from threading import Thread, Lock
from typing import Self, Literal, Iterable, Any, Callable
import hmac
from urllib.parse import urljoin

from httpx import AsyncClient, HTTPError
import xmltodict
from fastapi import FastAPI, Request, Response, APIRouter
from uvicorn import Config, Server
from pyngrok import ngrok
from pyexpat import ExpatError

from ytnoti.enums import NotificationKind
from ytnoti.models import YouTubeNotifierConfig
from ytnoti.models.notification import Notification, Channel, Thumbnail, Video, Stats, Timestamp
from ytnoti.types import PushNotificationListener, ReadyListener


class YouTubeNotifier:
    """
    A class that encapsulates the functionality for subscribing to YouTube channels and receiving push notifications.
    """

    _ALL_LISTENER_KEY = "_all"

    def __init__(self, *, callback_url: str = None, password: str = None, cache_size: int = 5000) -> None:
        """
        Create a new YouTubeNotifier instance.

        :param callback_url: The URL to receive push notifications. If not provided, ngrok will be used to create a
                             temporary URL.
        :param password: The password to use for verifying push notifications. If not provided, a random password will
                         be generated.
        :param cache_size: The number of video IDs to keep in the cache to prevent duplicate notifications.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = YouTubeNotifierConfig(
            callback_url,
            password or str("".join(random.choice(string.ascii_letters) for _ in range(20))),
            cache_size
        )
        self._listeners: dict[NotificationKind, dict[str, list[PushNotificationListener]]] = \
            {kind: {} for kind in NotificationKind}
        self._is_ready = False
        self._ready_lock = Lock()
        self._subscribed_ids: set[str] = set()
        self._seen_video_ids: OrderedDict[str, None] = OrderedDict()

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
        with self._ready_lock:
            return self._is_ready

    def listener(self, *, kind: NotificationKind, channel_ids: str | Iterable[str] = None) \
            -> Callable[[PushNotificationListener], PushNotificationListener]:
        """
        A decorator to add a listener for push notifications.

        :param kind: The kind of notification to listen for.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        :raises ValueError: If the channel ID is '_all'.
        """

        def decorator(func: PushNotificationListener) -> PushNotificationListener:
            self.add_listener(func, kind, channel_ids)

            return func

        return decorator

    def any(self, *, channel_ids: str | Iterable[str] = None) \
            -> Callable[[PushNotificationListener], PushNotificationListener]:
        """
        A decorator to add a listener for any kind of push notification.
        Alias for @listener(kind=NotificationKind.ANY).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """

        return self.listener(kind=NotificationKind.ANY, channel_ids=channel_ids)

    def upload(self, *, channel_ids: str | Iterable[str] = None) \
            -> Callable[[PushNotificationListener], PushNotificationListener]:
        """
        A decorator to add a listener for when a video is uploaded.
        Alies for @listener(kind=NotificationKind.UPLOAD).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """

        return self.listener(kind=NotificationKind.UPLOAD, channel_ids=channel_ids)

    def edit(self, *, channel_ids: str | Iterable[str] = None) \
            -> Callable[[PushNotificationListener], PushNotificationListener]:
        """
        A decorator to add a listener for when a video is edited.
        Alies for @listener(kind=NotificationKind.EDIT).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """

        return self.listener(kind=NotificationKind.EDIT, channel_ids=channel_ids)

    def add_listener(self,
                     func: PushNotificationListener,
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
            self._logger.debug("Added %s listener (%s) for all channels", kind.name, func.__name__)
            return self

        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]

        for channel_id in channel_ids:
            if channel_id == self._ALL_LISTENER_KEY:
                raise ValueError(f"Channel ID cannot be '{self._ALL_LISTENER_KEY}'")

            self._get_listeners(kind, channel_id).append(func)
            self._logger.debug("Added %s listener (%s) for channel: %s", kind.name,func.__name__, channel_id)

        return self

    def add_any_listener(self, func: PushNotificationListener, channel_ids: str | Iterable[str] = None) -> Self:
        """
        Add a listener for any kind of push notification.
        Alias for add_listener(func, NotificationKind.ANY, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        return self.add_listener(func, NotificationKind.ANY, channel_ids)

    def add_upload_listener(self, func: PushNotificationListener, channel_ids: str | Iterable[str] = None) -> Self:
        """
        Add a listener for when a video is uploaded.
        Alias for add_listener(func, NotificationKind.UPLOAD, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        return self.add_listener(func, NotificationKind.UPLOAD, channel_ids)

    def add_edit_listener(self, func: PushNotificationListener, channel_ids: str | Iterable[str] = None) -> Self:
        """
        Add a listener for when a video is edited.
        Alias for add_listener(func, NotificationKind.EDIT, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        return self.add_listener(func, NotificationKind.EDIT, channel_ids)

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

        not_subscribed = set(channel_ids).difference(self._subscribed_ids)
        asyncio.get_running_loop().create_task(self._subscribe(not_subscribed))

        return self

    def _mark_as_seen(self, video_id: str) -> Self:
        """
        Mark a video as seen to prevent duplicate notifications.

        :param video_id: The video ID to mark as seen.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        if len(self._seen_video_ids) > self._config.cache_size:
            self._seen_video_ids.popitem(last=False)

        self._seen_video_ids[video_id] = None

        return self

    def _get_kind(self, notification: Notification) -> NotificationKind:
        """
        Get the kind of notification based on the video ID.

        :param notification: The notification to get the kind for.
        :return: The kind of notification.
        """

        return NotificationKind.EDIT if notification.video.id in self._seen_video_ids else NotificationKind.UPLOAD

    def _get_listeners(self, kind: NotificationKind, channel_id: str | None) -> list[PushNotificationListener]:
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

    def run(self, *, port: int = 8000, endpoint: str = "/", app: FastAPI = None, **kwargs: Any) -> None:
        """
        Run the notifier to receive push notifications. This method will block until the notifier is stopped.

        :param port: The port to run the server on.
        :param endpoint: The endpoint to receive push notifications.
        :param app: The FastAPI app to use. If not provided, a new app will be created.
        :param kwargs: Additional arguments to pass to the server configuration.
        """

        if app is None:
            app = FastAPI()

        is_ngrok = False
        if self._config.callback_url is None:
            is_ngrok = True
            self._config.callback_url = ngrok.connect(str(port)).public_url

        self._config.callback_url = urljoin(self._config.callback_url, endpoint)
        self._logger.info("Callback URL: %s", self._config.callback_url)

        router = APIRouter()
        router.add_api_route(urljoin(endpoint, "health"), self._health, methods=["HEAD", "GET"])
        router.add_api_route(endpoint, self._get, methods=["GET"])
        router.add_api_route(endpoint, self._post, methods=["POST"])
        app.include_router(router)

        async def on_ready():
            while not await self._is_listening():
                await asyncio.sleep(0.1)

            await self._subscribe(self._subscribed_ids)

        async def repeat_subscribe(interval: float):
            while True:
                await asyncio.sleep(interval)
                await self._subscribe(self._subscribed_ids)

        app.add_event_handler("startup", lambda: asyncio.create_task(on_ready()))
        app.add_event_handler("startup", lambda: asyncio.create_task(repeat_subscribe(60 * 60 * 24)))

        config = Config(app, "0.0.0.0", port, log_level="warning", **kwargs)
        server = Server(config)

        sigint = False

        def signal_handler(*_):
            nonlocal sigint
            sigint = True

            # ngrok is already stopped at this point, so we can't unsubscribe if we are using ngrok.
            # It might not be matter though because ngrok generates unique URL every time, and the old URL will be
            # invalid.
            if not is_ngrok:
                asyncio.run(self._subscribe(self._subscribed_ids, mode="unsubscribe"))

            server.should_exit = True

        self._logger.debug("Currently registered listeners: %s", self._listeners)

        # Run the server in a separate thread to catch signals
        server_thread = Thread(target=server.run, daemon=True)
        server_thread.start()
        signal.signal(signal.SIGINT, signal_handler)

        while not sigint:
            signal.pause()

        server_thread.join()

    async def _is_listening(self) -> bool:
        """
        Check if the server is listening for push notifications.

        :return: True if the server is listening, False otherwise.
        """

        try:
            async with AsyncClient() as client:
                response = await client.head(urljoin(self._config.callback_url, "health"))
        except ConnectionError:
            return False

        return response.status_code == HTTPStatus.OK.value

    async def _subscribe(self, channel_ids: Iterable[str], *, mode: Literal["subscribe", "unsubscribe"] = "subscribe"):
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
                self._logger.debug("Sending %s request for channel: %s", mode, channel_id)

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
                raise HTTPError(f"Failed to {mode} channel ({channel_id}) with status code {response.status_code}")

            self._logger.info("Successfully %sd channel: %s", mode, channel_id)

    @staticmethod
    async def _health():
        """
        Health check endpoint.
        """
        return Response()

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

        self._logger.debug("Received push notification: %s", body)

        try:
            # entry can be list of dict or just dict
            entries = body["feed"]["entry"] if isinstance(body["feed"]["entry"], list) else [body["feed"]["entry"]]

            for entry in entries:
                channel = Channel(
                    id=body["feed"]["yt:channelId"],
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
                    description=entry["media:group"]["media:description"],
                    url=entry["link"]["@href"],
                    thumbnail=thumbnail,
                    stats=stats,
                    timestamp=timestamp
                )

                notification = Notification(channel, video)
                kind = self._get_kind(notification)
                listeners = (self._get_listeners(kind, None) +
                             self._get_listeners(kind, channel.id) +
                             self._get_listeners(NotificationKind.ANY, None) +
                             self._get_listeners(NotificationKind.ANY, channel.id))

                for func in listeners:
                    await func(notification)

                self._mark_as_seen(video.id)
        except (TypeError, KeyError, ValueError):
            self._logger.exception("Failed to parse request body: %s", body)
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
