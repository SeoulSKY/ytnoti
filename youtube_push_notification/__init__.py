import asyncio
import logging
import random
import signal
import string
import subprocess
import sys
import time
from asyncio import CancelledError
from datetime import datetime
from http import HTTPStatus
from multiprocessing import Process, Manager
from pyexpat import ExpatError
from threading import Thread, Lock
from types import FrameType
from typing import Self, Literal

import xmltodict
import requests
import uvicorn
from fastapi import FastAPI, Request, Response, APIRouter
from contextlib import asynccontextmanager

from pyngrok import ngrok
from requests import HTTPError
from starlette.types import Lifespan, ASGIApp, Scope, Receive, Send
from uvicorn import Config, Server

from youtube_push_notification.models import PushNotification, Channel, Thumbnail, Video, VideoStats
from youtube_push_notification.types import PushNotificationListener, ReadyListener


class YouTubePushNotifier:

    def __init__(self, *, callback_url: str, endpoint: str = "/", port: int = 8000, password_length: int = 20,
                 log_level: int = logging.INFO):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._callback_url = callback_url
        self._endpoint = endpoint
        self._port = port
        self._password = "".join(random.choice(string.ascii_letters) for _ in range(password_length))
        self._channel_listeners: dict[str, list[PushNotificationListener]] = {}
        self._ready_listeners: list[ReadyListener] = []
        self._is_ready = False
        self._ready_lock = Lock()

        self._logger.setLevel(log_level)

    @property
    def callback_url(self) -> str:
        return self._callback_url

    def listener(self, *, channel_ids: list[str]):
        async def subscribe():
            await self._subscribe(channel_ids)

        def decorator(func: PushNotificationListener) -> PushNotificationListener:
            self.add_channel_listener(func, channel_ids)

            return func

        with self._ready_lock:
            if self._is_ready:
                asyncio.get_event_loop().run_until_complete(subscribe())
            else:
                self.add_ready_listener(subscribe)

        return decorator

    def ready(self, func: ReadyListener) -> ReadyListener:
        self.add_ready_listener(func)
        return func

    def add_channel_listener(self, func: PushNotificationListener, channel_ids: list[str]) -> Self:
        for channel_id in channel_ids:
            if channel_id not in self._channel_listeners:
                self._channel_listeners[channel_id] = []

            self._channel_listeners[channel_id].append(func)

        return self

    def add_ready_listener(self, func: ReadyListener) -> Self:
        self._ready_listeners.append(func)
        return self

    @staticmethod
    def _run_ngrok(port: int, return_dict: dict):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        tunnel = ngrok.connect(addr=str(port))
        return_dict["url"] = tunnel.public_url

    def run(self, *, app: FastAPI = None, **kwargs):
        if app is None:
            app = FastAPI()

        self._logger.info(f"Callback URL: {self._callback_url + self._endpoint}")

        router = APIRouter()
        router.add_api_route(self._endpoint, self._get, methods=["GET"])
        router.add_api_route(self._endpoint, self._post, methods=["POST"])
        app.include_router(router)

        async def handle_ready():
            await self._wait_until_ready()

            try:
                for func in self._ready_listeners:
                    await func()
            except Exception as ex:
                self._logger.exception(ex)
            finally:
                self._ready_listeners.clear()

        async def repeat_subscribe(interval: float):
            while True:
                await asyncio.sleep(interval)
                await self._subscribe(self._channel_listeners.keys())

        app.add_event_handler("startup", lambda: asyncio.create_task(handle_ready()))
        app.add_event_handler("startup", lambda: asyncio.create_task(repeat_subscribe(60 * 60 * 24)))

        config = Config(app=app, host="0.0.0.0", port=self._port, log_level=self._logger.level, **kwargs)
        server = Server(config)

        sigint = False

        def signal_handler(*_):
            nonlocal sigint
            sigint = True

            asyncio.run(self._subscribe(self._channel_listeners.keys(), mode="unsubscribe"))
            server.should_exit = True

        server_thread = Thread(target=server.run, daemon=True)
        server_thread.start()
        signal.signal(signal.SIGINT, signal_handler)

        while not sigint:
            signal.pause()

        server_thread.join()

    async def _wait_until_ready(self):
        sleep_amount = 0.1

        # Wait until the server starts listening
        while True:
            try:
                await asyncio.to_thread(requests.get, f"http://localhost:{self._port}", {"healthcheck": True})
                with self._ready_lock:
                    self._is_ready = True
                break
            except ConnectionError:
                await asyncio.sleep(sleep_amount)

    async def _subscribe(self, channel_ids, *, mode: Literal["subscribe", "unsubscribe"] = "subscribe"):
        for channel_id in channel_ids:
            self._logger.debug(f"Sending {mode} request for channel: {channel_id}")

            response = await asyncio.to_thread(
                requests.post,
                "https://pubsubhubbub.appspot.com",
                {
                    "hub.mode": mode,
                    "hub.topic": f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                    "hub.callback": self._callback_url,
                    "hub.verify": "sync",
                    "hub.secret": "",
                    "hub.lease_seconds": "",
                    "hub.verify_token": ""
                },
                headers={"Content-type": "application/x-www-form-urlencoded"})

            if response.status_code != HTTPStatus.NO_CONTENT.value:
                raise HTTPError(f"Failed to {mode} channel ({channel_id}) with status code {response.status_code}")

            self._logger.info(f"Successfully {mode}d channel: {channel_id}")

    @staticmethod
    async def _get(request: Request):
        if "healthcheck" in request.query_params:
            return Response()

        challenge = request.query_params.get("hub.challenge")
        if challenge is None:
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        return Response(challenge)

    async def _post(self, request: Request):
        try:
            body = xmltodict.parse((await request.body()))
        except ExpatError:
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        for entry in body["feed"]["entry"]:
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
                stats = VideoStats(
                    likes=int(entry["media:group"]["media:community"]["media:starRating"]["@count"]),
                    views=int(entry["media:group"]["media:community"]["media:statistics"]["@views"]),
                )

            video = Video(
                id=entry["yt:videoId"],
                title=entry["title"],
                description=entry["media:group"]["media:description"],
                url=entry["link"]["@href"],
                thumbnail=thumbnail,
                stats=stats,
                timestamp=datetime.strptime(entry["updated"], "%Y-%m-%dT%H:%M:%S%z")
            )

            notification = PushNotification(channel, video)

            for func in self._channel_listeners[channel.id]:
                await func(notification)

        return Response(status_code=HTTPStatus.NO_CONTENT.value)
