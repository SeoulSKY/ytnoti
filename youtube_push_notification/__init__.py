import logging
import random
import string
import time
from datetime import datetime
from http import HTTPStatus
from inspect import signature, iscoroutinefunction
from pyexpat import ExpatError
from threading import Thread

import xmltodict
import requests
import uvicorn
from fastapi import FastAPI, Request, Response, APIRouter

from pyngrok import ngrok

from youtube_push_notification.models import PushNotification, Channel, Thumbnail, Video, VideoStats
from youtube_push_notification.types import PushNotificationListener


class YouTubePushNotifier:

    def __init__(self, *, callback_url: str = None, password_length: int = 20):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._callback_url = callback_url
        self._password = "".join(random.choice(string.ascii_letters) for _ in range(password_length))
        self._event_listeners: list[PushNotificationListener] = []
        self._channel_listeners: dict[str, PushNotificationListener] = {}

    @property
    def callback_url(self) -> str | None:
        return self._callback_url

    def listener(self, *, channel_id: str = None):
        def decorator(func: PushNotificationListener) -> PushNotificationListener:
            if not callable(func) or not iscoroutinefunction(func):
                raise TypeError("This decorator is for async function")

            sig = signature(func)
            if len(sig.parameters) != 1 or not issubclass(next(iter(sig.parameters.values())).annotation,
                                                          PushNotification):
                raise TypeError("This decorator is for async function that takes a PushNotification as argument")

            self._event_listeners.append(func)
            if channel_id is not None:
                self._channel_listeners[channel_id] = func

            return func

        return decorator

    def run(self, channel_ids: list[str], *, endpoint: str = "/", port: int = 8000, app: FastAPI = None):
        if app is None:
            app = FastAPI()

        if self._callback_url is None:
            self._callback_url = ngrok.connect(addr=str(port)).public_url

        print("callback_url: ", self._callback_url)

        router = APIRouter()

        router.add_api_route(endpoint, self._get, methods=["GET"])
        router.add_api_route(endpoint, self._post, methods=["POST"])

        app.include_router(router)

        Thread(target=self.__thread_target, args=(channel_ids,), daemon=True).start()
        uvicorn.run(app, host="0.0.0.0", port=port)

    def __thread_target(self, channel_ids: list[int]):
        sleep_amount = 0.1
        # Wait until the server starts listening
        while True:
            if self._callback_url is None:
                time.sleep(sleep_amount)
                continue

            try:
                requests.get(self.callback_url)
                break
            except ConnectionError:
                time.sleep(sleep_amount)

        try:
            self._subscribe(channel_ids)
        except Exception as ex:
            print(ex)

    def _subscribe(self, channel_ids):
        for channel_id in channel_ids:
            response = requests.post(
                "https://pubsubhubbub.appspot.com/subscribe",
                data={
                    "hub.mode": "subscribe",
                    "hub.topic": f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}",
                    "hub.callback": self._callback_url,
                    "hub.verify": "sync",
                    "hub.secret": self._password,
                    "hub.lease_seconds": "",
                    "hub.verify_token": ""
                },
                headers={"Content-type": "application/x-www-form-urlencoded"})

            if response.status_code != HTTPStatus.NO_CONTENT.value:
                raise ValueError(f"Failed to subscribe channel: {channel_id}")

    @staticmethod
    async def _get(request: Request):
        challenge = request.query_params.get("hub.challenge")
        if challenge is None:
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        return Response(challenge)

    async def _post(self, request: Request):
        try:
            body = xmltodict.parse((await request.body()))
        except ExpatError:
            return Response(status_code=HTTPStatus.BAD_REQUEST.value)

        print("body:", body)

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

            for func in self._event_listeners + [self._channel_listeners[channel.id]]:
                await func(notification)

        return Response(status_code=HTTPStatus.NO_CONTENT.value)
