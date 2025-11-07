"""Contains the YouTubePushNotifier class which is used to subscribe to
YouTube channels and receive push notifications when new videos are uploaded or old
videos are updated.
"""

__all__ = [
    "AsyncYouTubeNotifier",
    "Channel",
    "NotificationKind",
    "NotificationListener",
    "Timestamp",
    "Video",
    "YouTubeNotifier",
    "YouTubeNotifierConfig",
]

import asyncio
import hmac
import logging
import secrets
import signal
import string
import time
import warnings
from asyncio import Task
from collections.abc import (
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Iterable,
    Iterator,
)
from contextlib import asynccontextmanager, contextmanager, suppress
from datetime import datetime, timedelta
from http import HTTPStatus
from pyexpat import ExpatError
from threading import Thread
from typing import Any, Literal, Self
from urllib.parse import urlparse

import xmltodict
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.routing import APIRoute
from httpx import AsyncClient
from pyngrok import ngrok
from pyngrok.exception import PyngrokNgrokURLError
from starlette.routing import Route
from uvicorn import Config, Server

from ytnoti.enums import NotificationKind
from ytnoti.errors import HTTPError
from ytnoti.models.history import InMemoryVideoHistory, VideoHistory
from ytnoti.models.video import Channel, Timestamp, Video
from ytnoti.types import NotificationListener, T


class AsyncYouTubeNotifier:
    """A class that encapsulates the functionality for subscribing to YouTube
    channels and receiving push notifications.
    """

    _ALL_LISTENER_KEY = "_all"
    _UPLOAD_EVENT_THRESHOLD = timedelta(seconds=20)

    def __init__(
        self,
        *,
        callback_url: str | None = None,
        password: str | None = None,
        video_history: VideoHistory | None = None,
    ) -> None:
        """Set up the YouTubeNotifier instance.

        :param callback_url: The URL to receive push notifications.
            If not provided, ngrok will be used to create a temporary URL.
        :param password: The password to use for verifying push notifications.
            If not provided, a random password will be generated.
        :param video_history: The video history to use to prevent duplicate
            notifications.
            If not provided,
            a new instance of InMemoryVideoHistory will be created and used.
        """
        self._logger = logging.getLogger(self.__class__.__name__)

        self._callback_url = callback_url
        self._host = ""
        self._port = -1
        self._app = FastAPI()
        self._using_ngrok = callback_url is None
        self._password = password or str(
            "".join(secrets.choice(string.ascii_letters) for _ in range(20))
        )

        self._listeners: dict[
            NotificationKind, dict[str, list[NotificationListener]]
        ] = {kind: {} for kind in NotificationKind}
        self._subscribed_ids: set[str] = set()
        self._video_history = video_history or InMemoryVideoHistory()
        self._server: Server | None = None
        self._lock = asyncio.Lock()

    @property
    def callback_url(self) -> str | None:
        """Get the callback URL. If the callback URL was not provided when creating
        the instance, it will become available after the notifier is started.

        :return: The callback URL.
        """
        return self._callback_url

    @property
    def is_ready(self) -> bool:
        """Check if the notifier is ready to receive push notifications.

        :return: True if the notifier is ready, False otherwise.
        """
        return self._server is not None

    def listener(  # pragma: no cover
        self, *, kind: NotificationKind, channel_ids: str | Iterable[str] | None = None
    ) -> Callable[[NotificationListener], NotificationListener]:
        """Decorate the function to add a listener for push notifications.

        .. deprecated:: 2.1.0
            This method has been deprecated in favor of the more specific decorators:
            :meth:`upload`, :meth:`edit`, and :meth:`any`.
            It will be removed in version 3.0.0.

        :param kind: The kind of notification to listen for.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        :raises ValueError: If the channel ID is '_all'.
        """
        warnings.warn(
            "listener() is deprecated since version 2.1.0 and will be removed "
            "in version 3.0.0. Use upload(), edit(), or any() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self._listener(kind=kind, channel_ids=channel_ids)

    def _listener(
        self, *, kind: NotificationKind, channel_ids: str | Iterable[str] | None = None
    ) -> Callable[[NotificationListener], NotificationListener]:
        """Decorate the function to add a listener for push notifications.

        .. deprecated:: 2.1.0
            This method has been deprecated in favor of the more specific decorators:
            :meth:`upload`, :meth:`edit`, and :meth:`any`.
            It will be removed in version 3.0.0.

        :param kind: The kind of notification to listen for.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        :raises ValueError: If the channel ID is '_all'.
        """

        def decorator(func: NotificationListener) -> NotificationListener:
            self._add_listener(func, kind, channel_ids)

            return func

        return decorator

    def any(
        self, *, channel_ids: str | Iterable[str] | None = None
    ) -> Callable[[NotificationListener], NotificationListener]:
        """Decorate the function to add a listener for any kind of push notification.
        Alias for @listener(kind=NotificationKind.ANY).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """
        return self._listener(kind=NotificationKind.ANY, channel_ids=channel_ids)

    def upload(
        self, *, channel_ids: str | Iterable[str] | None = None
    ) -> Callable[[NotificationListener], NotificationListener]:
        """Decorate the function to add a listener for when a video is uploaded.
        Alies for @listener(kind=NotificationKind.UPLOAD).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """
        return self._listener(kind=NotificationKind.UPLOAD, channel_ids=channel_ids)

    def edit(
        self, *, channel_ids: str | Iterable[str] | None = None
    ) -> Callable[[NotificationListener], NotificationListener]:
        """Decorate the function to add a listener for when a video is edited.
        Alies for @listener(kind=NotificationKind.EDIT).

        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The decorator function.
        """
        return self._listener(kind=NotificationKind.EDIT, channel_ids=channel_ids)

    def add_listener(
        self,
        func: NotificationListener,
        kind: NotificationKind,
        channel_ids: str | Iterable[str] | None = None,
    ) -> Self:  # pragma: no cover
        """Add a listener for push notifications.

        .. deprecated:: 2.1.0
            This method has been deprecated in favor of the more specific decorators:
            :meth:`add_upload_listener`, :meth:`add_edit_listener`,
            and :meth:`add_any_listener`.
            It will be removed in version 3.0.0.

        :param func: The listener function to add.
        :param kind: The kind of notification to listen for.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        :raises ValueError: If the channel ID is '_all'.
        """
        warnings.warn(
            "add_listener() is deprecated since version 2.1.0 and will be removed "
            "in version 3.0.0. Use add_upload_listener(), add_edit_listener(), "
            "or add_any_listener() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        return self._add_listener(func, kind, channel_ids)

    def _add_listener(
        self,
        func: NotificationListener,
        kind: NotificationKind,
        channel_ids: str | Iterable[str] | None = None,
    ) -> Self:
        """Add a listener for push notifications.

        .. deprecated:: 2.1.0
            This method has been deprecated in favor of the more specific decorators:
            :meth:`add_upload_listener`, :meth:`add_edit_listener`,
            and :meth:`add_any_listener`.
            It will be removed in version 3.0.0.

        :param func: The listener function to add.
        :param kind: The kind of notification to listen for.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        :raises ValueError: If the channel ID is '_all'.
        """
        if channel_ids is None:
            self._get_listeners(kind, None).append(func)
            self._logger.debug(
                "Added %s listener (%s) for all channels", kind.name, func.__name__
            )
            return self

        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]

        for channel_id in channel_ids:
            if channel_id == self._ALL_LISTENER_KEY:
                message = f"Channel ID cannot be '{self._ALL_LISTENER_KEY}'"
                raise ValueError(message)

            self._get_listeners(kind, channel_id).append(func)
            self._logger.debug(
                "Added %s listener (%s) for channel: %s",
                kind.name,
                func.__name__,
                channel_id,
            )

        return self

    def add_any_listener(
        self, func: NotificationListener, channel_ids: str | Iterable[str] | None = None
    ) -> Self:
        """Add a listener for any kind of push notification.
        Alias for add_listener(func, NotificationKind.ANY, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """
        return self._add_listener(func, NotificationKind.ANY, channel_ids)

    def add_upload_listener(
        self, func: NotificationListener, channel_ids: str | Iterable[str] | None = None
    ) -> Self:
        """Add a listener for when a video is uploaded.
        Alias for add_listener(func, NotificationKind.UPLOAD, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """
        return self._add_listener(func, NotificationKind.UPLOAD, channel_ids)

    def add_edit_listener(
        self, func: NotificationListener, channel_ids: str | Iterable[str] | None = None
    ) -> Self:
        """Add a listener for when a video is edited.
        Alias for add_listener(func, NotificationKind.EDIT, channel_ids).

        :param func: The listener function to add.
        :param channel_ids: The channel ID(s) to listen for.
            If not provided, the listener will be called for all channels.
        :return: The YouTubeNotifier instance to allow for method chaining.
        """
        return self._add_listener(func, NotificationKind.EDIT, channel_ids)

    def _get_listeners(
        self, kind: NotificationKind, channel_id: str | None
    ) -> list[NotificationListener]:
        """Get the listeners for the given kind and channel ID.

        :param kind: The kind of notification.
        :param channel_id: The channel ID to get the listeners for.
            If not provided, the listeners for all channels
        :return: The listeners for the given kind and channel ID.
        """
        key = channel_id or self._ALL_LISTENER_KEY
        listeners = self._listeners[kind].get(key, None)
        if listeners is None:
            listeners = []
            self._listeners[kind][key] = listeners

        return listeners

    def _get_router(self) -> APIRouter:
        """Get the FastAPI router for the notifier.

        :return: The FastAPI router.
        """
        router = APIRouter()
        endpoint = urlparse(self._callback_url).path or "/"
        router.add_api_route(endpoint, self._get, methods=["HEAD", "GET"])
        router.add_api_route(endpoint, self._post, methods=["POST"])

        return router

    def _get_server_config(self, **configs: object) -> Config:
        """Get the server configuration.

        :param configs: Additional arguments to pass to the server configuration.
        :return: The server configuration.
        """
        return Config(self._app, self._host, self._port, **configs)  # ty: ignore[invalid-argument-type]

    def _get_server(
        self,
        *,
        host: str,
        port: int,
        app: FastAPI | None = None,
        **configs: object,
    ) -> Server:
        """Create a server instance to receive push notifications.

        :param host: The host to run the server on.
        :param port: The port to run the server on.
        :param app: The FastAPI app to use. If not provided, a new app will be created.
        :param log_level: The log level to use for the uvicorn server.
        :param configs: Additional arguments to pass to the server configuration.
        :return: The server instance.
        :raises ValueError: If the given app instance has a route that conflicts with
            the notifier's routes.
        """
        self._host = host
        self._port = port
        self._app = app or self._app

        if self._using_ngrok:
            self._callback_url = ngrok.connect(str(port)).public_url

        self._logger.info("Callback URL: %s", self._callback_url)

        endpoint = urlparse(self._callback_url).path or "/"

        if any(
            isinstance(route, APIRoute | Route) and route.path == endpoint
            for route in self._app.routes
        ):
            raise ValueError(
                f"Endpoint {endpoint} is reserved for {__package__} "
                f"so it cannot be used by the app"
            )

        self._app.include_router(self._get_router())

        async def on_ready() -> None:
            while True:
                await asyncio.sleep(0.1)

                try:
                    async with AsyncClient() as client:
                        response = await client.head(
                            self._callback_url, params={"hub.challenge": "1"}
                        )
                        if response.status_code == HTTPStatus.OK:
                            break
                except ConnectionError:  # pragma: no cover
                    continue

            self._server = server

            await self._register(self._subscribed_ids)

        async def task() -> None:  # pragma: no cover
            try:
                await self._register(self._subscribed_ids)
            except RuntimeError:
                self._logger.exception("")

        self._app.add_event_handler("startup", lambda: asyncio.create_task(on_ready()))
        self._app.add_event_handler(
            "startup",
            lambda: asyncio.create_task(self._repeat_task(task, 60 * 60 * 24)),
        )

        server = Server(self._get_server_config(**configs))
        return server

    async def _repeat_task(
        self,
        task: Callable[[], Awaitable[None]],
        interval: float,
        predicate: Callable[[], bool] | None = None,
    ) -> None:
        """Repeatedly run a task.

        :param task: The coroutine to repeat
        :param interval: The interval in seconds to repeat the task
        :param predicate: An optional predicate function
            that returns True to continue
        """
        while not predicate or predicate():
            await asyncio.sleep(interval)
            try:
                await task()
            except Exception:
                self._logger.exception("Failed to repeat task")

    async def serve(
        self,
        *,
        host: str = "0.0.0.0",  # noqa: S104
        port: int = 8000,
        log_level: int = logging.WARNING,
        app: FastAPI | None = None,
        **configs: object,
    ) -> None:  # pragma: no cover
        """Start the FastAPI server to receive push notifications in an existing event
            loop and wait until the server stops.

        .. deprecated:: 2.1.0
        Use :meth:`run` instead.

        :param host: The host to run the FastAPI server on.
        :param port: The port to run the FastAPI server on.
        :param log_level: The log level to use for the uvicorn server.
        :param app: The FastAPI app instance to use. If not provided, a new instance
            will be created.
        :param configs: Additional arguments to pass to the Config class of uvicorn.
        :raises ValueError: If the given app instance has a route that conflicts with
            the notifier's routes.
        """
        warnings.warn(
            "serve() is deprecated and will be removed in "
            "version 3.0.0. Use run() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        await self.run(host=host, port=port, log_level=log_level, app=app, **configs)

    async def run(
        self,
        *,
        host: str = "0.0.0.0",  # noqa: S104
        port: int = 8000,
        log_level: int = logging.WARNING,
        app: FastAPI | None = None,
        **configs: object,
    ) -> None:
        """Start the FastAPI server to receive push notifications in an existing event
            loop and wait until the server stops.

        :param host: The host to run the FastAPI server on.
        :param port: The port to run the FastAPI server on.
        :param log_level: The log level to use for the uvicorn server.
        :param app: The FastAPI app instance to use. If not provided, a new instance
            will be created.
        :param configs: Additional arguments to pass to the Config class of uvicorn.
        :raises ValueError: If the given app instance has a route that conflicts with
            the notifier's routes.
        """
        server = self._get_server(
            host=host, port=port, app=app, log_level=log_level, **configs
        )

        old_signal_handler = signal.getsignal(signal.SIGINT)

        async def signal_handler() -> None:  # pragma: no cover
            await self._on_exit()

            signal.signal(signal.SIGINT, old_signal_handler)

        signal.signal(
            signal.SIGINT, lambda _sig, _frame: asyncio.create_task(signal_handler())
        )

        try:
            await server.serve()
        except KeyboardInterrupt:  # pragma: no cover
            await self._on_exit()

    @asynccontextmanager
    async def run_in_background(
        self,
        *,
        host: str = "0.0.0.0",  # noqa: S104
        port: int = 8000,
        app: FastAPI | None = None,
        log_level: int = logging.WARNING,
        **configs: object,
    ) -> AsyncIterator[Task]:
        """Run the FastAPI server in an existing event loop and return immediately.

        :param host: The host IP address to bind the server.
        :param port: The port number to bind the server.
        :param app: The FastAPI application to use for serving the server.
        :param log_level: The log level to use for the server.
        :param configs: Additional configurations to pass to the server.
        """
        task = asyncio.create_task(
            self.run(host=host, port=port, app=app, log_level=log_level, **configs)
        )
        try:
            while not self.is_ready:  # noqa: ASYNC110
                await asyncio.sleep(0.1)
            yield task
        finally:
            await self._on_exit()
            await task

    @staticmethod
    async def _verify_channel_ids(channel_ids: Iterable[str]) -> None:
        """Verify if the given channel IDs are valid.

        :param channel_ids: The channel IDs
        :raises ValueError: If the channel ID is invalid.
        """
        async with AsyncClient() as client:
            for channel_id in channel_ids:
                response = await client.head(
                    f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
                )
                if response.status_code != HTTPStatus.OK:
                    raise ValueError(f"Invalid channel ID: {channel_id}")

    async def subscribe(self, channel_ids: str | Iterable[str]) -> Self:
        """Subscribe to YouTube channels to receive push notifications.
        This is lazy and will subscribe when the notifier is ready.
        If the notifier is already ready, it will subscribe immediately.

        :param channel_ids: The channel ID(s) to subscribe to.
        :return: The current instance for method chaining.
        :raises ValueError: If the channel ID is invalid.
        :raises HTTPError: If failed to verify the channel ID or failed to subscribe
            due to an HTTP error.
        """
        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]

        await self._verify_channel_ids(channel_ids)

        if not self.is_ready:
            self._subscribed_ids.update(channel_ids)
            return self

        not_subscribed = set(channel_ids).difference(self._subscribed_ids)
        await self._register(not_subscribed)

        self._subscribed_ids.update(not_subscribed)

        return self

    async def unsubscribe(self, channel_ids: str | Iterable[str]) -> Self:
        """Unsubscribe from YouTube channels to stop receiving push notifications.

        :param channel_ids: The channel ID(s) to unsubscribe from.
        :return: The current instance for method chaining.
        :raises ValueError: If the channel_ids includes ids that are not subscribed
        """
        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]

        if not self._subscribed_ids.issuperset(channel_ids):
            channel_ids = set(channel_ids)
            raise ValueError(
                f"No such subscribed channel IDs: "
                f"{channel_ids.difference(self._subscribed_ids)}"
            )

        unsubscribe_ids = self._subscribed_ids.intersection(channel_ids)

        await self._register(unsubscribe_ids, mode="unsubscribe")

        self._subscribed_ids.difference_update(unsubscribe_ids)

        return self

    async def _register(
        self,
        channel_ids: Iterable[str],
        *,
        mode: Literal["subscribe", "unsubscribe"] = "subscribe",
    ) -> None:
        """Subscribe or unsubscribe to YouTube channels to receive push notifications.

        :param channel_ids: The channel ID(s) to subscribe or unsubscribe to.
        :param mode: The mode to use. Either 'subscribe' or 'unsubscribe'.
        :raises ValueError: If an invalid channel ID is provided.
        :raises ConnectionError: If this method is called while the server is not
            listening.
        :raises HTTPError: If failed to subscribe or unsubscribe due to an HTTP error.
        """
        for channel_id in channel_ids:
            async with AsyncClient() as client:
                self._logger.debug(
                    "Sending %s request for channel: %s", mode, channel_id
                )

                response = await client.post(
                    "https://pubsubhubbub.appspot.com",
                    data={
                        "hub.mode": mode,
                        "hub.topic": f"https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}",
                        "hub.callback": self._callback_url,
                        "hub.verify": "sync",
                        "hub.secret": self._password,
                        "hub.lease_seconds": "",
                        "hub.verify_token": "",
                    },
                    headers={"Content-type": "application/x-www-form-urlencoded"},
                )

            if response.status_code == HTTPStatus.CONFLICT:  # pragma: no cover
                if not self.is_ready:
                    raise ConnectionError(
                        f"Cannot {mode} while the server is not ready"
                    )

                raise HTTPError(
                    f"Failed to {mode} channel: {channel_id}. "
                    f"The reason might be because {self._callback_url} is "
                    f"inaccessible from the public internet",
                    response.status_code,
                )

            if response.status_code != HTTPStatus.NO_CONTENT:  # pragma: no cover
                raise HTTPError(
                    f"Failed to {mode} channel: {channel_id}", response.status_code
                )

            self._logger.info("Successfully %sd channel: %s", mode, channel_id)

    def stop(self) -> None:
        """Gracefully stop the FastAPI server and the notifier.
        If the notifier is not running, this method will do nothing.
        """
        if not self.is_ready or self._server is None:
            return

        self._server.should_exit = True
        self._server = None

        if self._using_ngrok and self._callback_url is not None:
            with suppress(PyngrokNgrokURLError):
                ngrok.disconnect(self._callback_url)

    async def _on_exit(self) -> None:
        """Perform a task after the notifier is stopped."""
        self.stop()

    @staticmethod
    async def _get(request: Request) -> Response:
        """Handle a challenge from the Google pubsubhubbub server."""
        challenge = request.query_params.get("hub.challenge")
        if challenge is None:
            return Response(status_code=HTTPStatus.BAD_REQUEST)

        return Response(challenge)

    async def _post(self, request: Request) -> Response:
        """Handle push notifications from the Google pubsubhubbub server."""
        if not await self._is_authorized(request):
            return Response(status_code=HTTPStatus.UNAUTHORIZED)

        body = await request.body()

        try:
            body = xmltodict.parse(body)
        except ExpatError:
            self._logger.debug("Received invalid request body: %s", body)
            return Response(status_code=HTTPStatus.BAD_REQUEST)

        self._logger.debug("Received push notification: %s", body)

        try:
            if "at:deleted-entry" in body["feed"]:
                self._logger.debug("Ignoring push notification for deleted video")
                return Response(status_code=HTTPStatus.NO_CONTENT)

            # entry can be list of dict or just dict
            entries = (
                body["feed"]["entry"]
                if isinstance(body["feed"]["entry"], list)
                else [body["feed"]["entry"]]
            )

            for entry in entries:
                channel_id = entry["yt:channelId"]
                if channel_id not in self._subscribed_ids:
                    await self.unsubscribe(channel_id)
                    continue

                channel = Channel(
                    id=channel_id,
                    name=entry["author"]["name"],
                    url=entry["author"]["uri"],
                )

                timestamp = Timestamp(
                    published=self._parse_timestamp(entry["published"]),
                    updated=self._parse_timestamp(entry["updated"]),
                )

                url = (
                    entry["link"][0]["@href"]
                    if isinstance(entry["link"], list)
                    else entry["link"]["@href"]
                )

                video_id = entry["yt:videoId"]

                video = Video(
                    id=video_id,
                    title=entry["title"],
                    url=url,
                    timestamp=timestamp,
                    channel=channel,
                )

                async with self._lock:
                    if (
                        timestamp.published == timestamp.updated
                        or not await self._video_history.has(video)
                    ):
                        kind = NotificationKind.UPLOAD
                        await self._video_history.add(video)
                    else:
                        kind = NotificationKind.EDIT

                self._logger.debug("Classified video (%s) as %s", video.id, kind)

                listeners = (
                    self._get_listeners(kind, None)
                    + self._get_listeners(kind, channel.id)
                    + self._get_listeners(NotificationKind.ANY, None)
                    + self._get_listeners(NotificationKind.ANY, channel.id)
                )

                for func in listeners:
                    await func(video)
        except (TypeError, KeyError, ValueError) as ex:
            raise RuntimeError(f"Failed to parse request body: {body}") from ex

        return Response(status_code=HTTPStatus.NO_CONTENT)

    @staticmethod
    def _parse_timestamp(timestamp: str) -> datetime:
        time, zone = timestamp.split("+", 1)

        # Remove fractional seconds if exists
        time = time.split(".", 1)[0]

        return datetime.strptime(f"{time}+{zone}", "%Y-%m-%dT%H:%M:%S%z")

    async def _is_authorized(self, request: Request) -> bool:
        if not self._password:
            return True

        x_hub_signature = request.headers.get("X-Hub-Signature")
        # Check if the header is missing or invalid
        if x_hub_signature is None or "=" not in x_hub_signature:
            return False

        algorithm, value = x_hub_signature.split("=")
        hash_obj = hmac.new(self._password.encode(), await request.body(), algorithm)
        return hmac.compare_digest(hash_obj.hexdigest(), value)


class YouTubeNotifier(AsyncYouTubeNotifier):
    """A class that encapsulates the functionality for subscribing to YouTube
    channels and receiving push notifications.
    """

    def __init__(
        self,
        *,
        callback_url: str | None = None,
        password: str | None = None,
        video_history: VideoHistory | None = None,
    ) -> None:
        """Create a new YouTubeNotifier instance.

        :param callback_url: The URL to receive push notifications.
            If not provided, ngrok will be used to create a temporary URL.
        :param password: The password to use for verifying push notifications.
            If not provided, a random password will be generated.
        :param video_history: The video history to use to prevent duplicate
            notifications.
            If not provided, a new instance of InMemoryVideoHistory will be created and
            used.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        super().__init__(
            callback_url=callback_url,
            password=password,
            video_history=video_history,
        )

    def subscribe(self, channel_ids: str | Iterable[str]) -> Self:  # noqa: D102
        self._run_coroutine(super().subscribe(channel_ids))
        return self

    def unsubscribe(self, channel_ids: str | Iterable[str]) -> Self:  # noqa: D102
        self._run_coroutine(super().unsubscribe(channel_ids))
        return self

    def run(
        self,
        *,
        host: str = "0.0.0.0",  # noqa: S104
        port: int = 8000,
        app: FastAPI | None = None,
        log_level: int = logging.WARNING,
        **configs: object,
    ) -> None:
        """Start the FastAPI server to receive push notifications in the
            current thread and wait until the server stops.

        :param host: The host to run the FastAPI server on.
        :param port: The port to run the FastAPI server on.
        :param log_level: The log level to use for the uvicorn server.
        :param app: The FastAPI app instance to use. If not provided, a new instance
            will be created.
        :param configs: Additional arguments to pass to the Config class of uvicorn.
        :raises ValueError: If the given app instance has a route that conflicts with
            the notifier's routes.
        """
        server = self._get_server(
            host=host, port=port, app=app, log_level=log_level, **configs
        )

        try:
            server.run()
        except KeyboardInterrupt:  # pragma: no cover
            pass
        finally:
            self._on_exit()

    def _on_exit(self) -> None:
        """Perform a task after the notifier is stopped."""
        self.stop()

    @contextmanager
    def run_in_background(
        self,
        *,
        host: str = "0.0.0.0",  # noqa: S104
        port: int = 8000,
        app: FastAPI | None = None,
        log_level: int = logging.WARNING,
        **configs: object,
    ) -> Iterator[Thread]:
        """Start the FastAPI server to receive push notifications in the separate
            thread and return immediately.

        :param host: The host to run the FastAPI server on.
        :param port: The port to run the FastAPI server on.
        :param log_level: The log level to use for the uvicorn server.
        :param app: The FastAPI app instance to use. If not provided, a new instance
            will be created.
        :param configs: Additional arguments to pass to the Config class of uvicorn.
        :return: A thread that runs the FastAPI server in the background.
        :raises ValueError: If the given app instance has a route that conflicts with
            the notifier's routes.
        """
        configs["host"] = host
        configs["port"] = port
        configs["app"] = app
        configs["log_level"] = log_level

        thread = Thread(target=self.run, kwargs=configs, daemon=True)
        thread.start()
        try:
            while not self.is_ready:
                time.sleep(0.1)
            yield thread
        finally:
            self.stop()
            thread.join()

    @staticmethod
    def _run_coroutine(coro: Coroutine[Any, Any, T]) -> T:
        """Run a coroutine in the event loop.

        :param coro: The coroutine to run.
        :return: The result of the coroutine.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        else:
            return loop.run_until_complete(coro)
