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

from ytnoti.models.notification import Notification, Channel, Thumbnail, Video, Stats, Timestamp
from ytnoti.types import PushNotificationListener, ReadyListener


class YouTubeNotifier:
    """
    A class that encapsulates the functionality for subscribing to YouTube channels and receiving push notifications.
    """

    _ALL_LISTENER_KEY = "_all"

    def __init__(self, *, callback_url: str = None) -> None:
        """
        Create a new YouTubeNotifier instance.
        :param callback_url: The URL to receive push notifications. If not provided, ngrok will be used to create a
        temporary URL.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._callback_url = callback_url
        self._password = "".join(random.choice(string.ascii_letters) for _ in range(20))
        self._channel_listeners: dict[str, list[PushNotificationListener]] = {}
        self._is_ready = False
        self._ready_lock = Lock()
        self._subscribed: set[str] = set()

    @property
    def callback_url(self) -> str | None:
        """
        Get the callback URL.

        :return: The callback URL.
        """
        return self._callback_url

    @property
    def is_ready(self) -> bool:
        """
        Check if the notifier is ready to receive push notifications.

        :return: True if the notifier is ready, False otherwise.
        """
        with self._ready_lock:
            return self._is_ready

    def listener(self, *, channel_ids: Iterable[str] = None)\
            -> Callable[[PushNotificationListener], PushNotificationListener]:
        """
        A decorator to add a listener for push notifications.

        :param channel_ids: The channel IDs to listen for.
            If not provided, the listener will be called for all channels.
        """

        def decorator(func: PushNotificationListener) -> PushNotificationListener:
            self.add_channel_listener(func, channel_ids)

            return func

        return decorator

    def add_channel_listener(self, func: PushNotificationListener, channel_ids: Iterable[str] = None) -> Self:
        """
        Add a listener for push notifications.

        :param func: The listener function to add.
        :param channel_ids: The channel IDs to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        if channel_ids is None:
            if self._ALL_LISTENER_KEY not in self._channel_listeners:
                self._channel_listeners[self._ALL_LISTENER_KEY] = []
            self._channel_listeners[self._ALL_LISTENER_KEY].append(func)

            self._logger.debug("Added listener (%s) for all channels", func.__name__)
            return self

        for channel_id in channel_ids:
            if channel_id not in self._channel_listeners:
                self._channel_listeners[channel_id] = []
            self._channel_listeners[channel_id].append(func)

            self._logger.debug("Added listener (%s) for channel: %s", func.__name__, channel_id)

        return self

    def subscribe(self, channel_ids: Iterable[str]) -> Self:
        """
        Subscribe to YouTube channels to receive push notifications.

        :param channel_ids: The channel IDs to subscribe to.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """

        if not self.is_ready:
            self._subscribed.update(channel_ids)
            return self

        not_subscribed = set(channel_ids).difference(self._subscribed)
        asyncio.get_running_loop().create_task(self._subscribe(not_subscribed))

        return self

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
        if self._callback_url is None:
            is_ngrok = True
            self._callback_url = ngrok.connect(str(port)).public_url

        self._callback_url = urljoin(self._callback_url, endpoint)

        self._logger.info("Callback URL: %s", self._callback_url)

        router = APIRouter()
        router.add_api_route(urljoin(endpoint, "health"), self._health, methods=["GET"])
        router.add_api_route(endpoint, self._get, methods=["GET"])
        router.add_api_route(endpoint, self._post, methods=["POST"])
        app.include_router(router)

        async def on_ready():
            while not await self._is_listening():
                await asyncio.sleep(0.1)

            await self._subscribe(self._subscribed)

        async def repeat_subscribe(interval: float):
            while True:
                await asyncio.sleep(interval)
                await self._subscribe(self._subscribed)

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
                asyncio.run(self._subscribe(self._subscribed, mode="unsubscribe"))

            server.should_exit = True

        # Run the server in a separate thread to catch signals
        server_thread = Thread(target=server.run, daemon=True)
        server_thread.start()
        signal.signal(signal.SIGINT, signal_handler)

        while not sigint:
            signal.pause()

        server_thread.join()

    async def _is_listening(self):
        try:
            async with AsyncClient() as client:
                response = await client.get(urljoin(self._callback_url, "health"))
        except ConnectionError:
            return False

        return response.status_code == HTTPStatus.OK.value

    async def _subscribe(self, channel_ids: Iterable[str], *, mode: Literal["subscribe", "unsubscribe"] = "subscribe"):
        for channel_id in channel_ids:
            self._logger.debug("Sending %s request for channel: %s", mode, channel_id)

            async with AsyncClient() as client:
                response = await client.post(
                    "https://pubsubhubbub.appspot.com",
                    data={
                        "hub.mode": mode,
                        "hub.topic": f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                        "hub.callback": self._callback_url,
                        "hub.verify": "sync",
                        "hub.secret": self._password,
                        "hub.lease_seconds": "",
                        "hub.verify_token": ""
                    },
                    headers={"Content-type": "application/x-www-form-urlencoded"}
                )

            if response.status_code == HTTPStatus.CONFLICT.value and not await self._is_listening():
                raise HTTPError(f"Cannot {mode} while the server is not listening")

            if response.status_code != HTTPStatus.NO_CONTENT.value:
                raise HTTPError(f"Failed to {mode} channel ({channel_id}) with status code {response.status_code}")

            self._logger.info("Successfully %sd channel: %s", mode, channel_id)

    @staticmethod
    async def _health():
        return Response()

    @staticmethod
    async def _get(request: Request):
        challenge = request.query_params.get("hub.challenge")
        if challenge is None:
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        return Response(challenge)

    async def _post(self, request: Request):
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

                for func in self._channel_listeners[self._ALL_LISTENER_KEY]:
                    await func(notification)

                if channel.id not in self._channel_listeners:
                    continue

                for func in self._channel_listeners[channel.id]:
                    await func(notification)
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
        hash_obj = hmac.new(self._password.encode(), await request.body(), algorithm)
        return hmac.compare_digest(hash_obj.hexdigest(), value)
