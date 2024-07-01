"""
This module contains the video history model.
"""

import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path
from threading import Lock

import aiofiles
from aiofiles import os, ospath

from ytnoti.models.video import Video, Channel


class VideoHistory(ABC):
    """
    Represents a history of videos.
    """

    @abstractmethod
    async def add(self, video: Video) -> None:
        """
        Add a video to the history.

        :param video: The video to add.
        """

    @abstractmethod
    async def has(self, video: Video) -> bool:
        """
        Check if a video is in the history.

        :param video: The video to check.
        :return: True if the video is in the history, False otherwise.
        """


class InMemoryVideoHistory(VideoHistory):
    """
    Represents an in-memory history of notifications.
    """

    def __init__(self, *, cache_size: int = 5000) -> None:
        """
        Create a new InMemoryVideoHistory instance.

        :param cache_size: The size of the cache. If the cache is full, the oldest video will be removed.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._video_ids: OrderedDict[str, None] = OrderedDict()
        self._cache_size = cache_size
        self._lock = Lock()

    @property
    def cache_size(self) -> int:
        """
        Get the size of the cache.

        :return: The size of the cache.
        """

        with self._lock:
            return self._cache_size

    @cache_size.setter
    def cache_size(self, value: int) -> None:
        with self._lock:
            self._logger.debug("Setting cache size to %d", value)
            self._cache_size = value

    async def add(self, video: Video) -> None:
        with self._lock:
            if video.id in self._video_ids:
                return

            if len(self._video_ids) >= self._cache_size:
                self._video_ids.popitem(last=False)

            self._logger.debug("Adding video (%s) to history", video.id)
            self._video_ids[video.id] = None

    async def has(self, video: Video) -> bool:
        with self._lock:
            return video.id in self._video_ids


class FileVideoHistory(VideoHistory):
    """
    Represents a file-based history of videos.
    """

    def __init__(self, *, dir_path: Path, num_videos: int = 100) -> None:
        """
        Create a new FileVideoHistory instance.

        :param dir_path: The path to the directory to store the history files
        :param num_videos: The number of videos to keep in the history file. If the number of videos exceeds this value,
                           the oldest videos will be removed.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._dir_path = dir_path
        self._num_videos = num_videos
        self._lock = Lock()

    def _get_path(self, channel: Channel) -> Path:
        """
        Get the path to the history file for a channel.

        :param channel: The channel to get the history file for.
        """

        return self._dir_path / channel.id

    async def _truncate(self, channel: Channel):
        """
        Truncate the history file for a channel.
        """

        path = self._get_path(channel)

        if not await ospath.exists(path):
            return

        async with aiofiles.open(path, "r", encoding="utf-8") as file:
            lines = await file.readlines()

        async with aiofiles.open(path, "w", encoding="utf-8") as file:
            await file.writelines(lines[-self._num_videos:])

    async def add(self, video: Video) -> None:
        await os.wrap(self._dir_path.mkdir)(parents=True, exist_ok=True)

        path = self._get_path(video.channel)

        with self._lock:
            await os.makedirs(path.parent, exist_ok=True)

            async with aiofiles.open(path, "a", encoding="utf-8") as file:
                self._logger.debug("Adding video (%s) to history at %s", video.id, path)
                await file.write(f"{video.id}\n")

            await self._truncate(video.channel)

    async def has(self, video: Video) -> bool:
        path = self._get_path(video.channel)

        with self._lock:
            if not await ospath.exists(path):
                return False

            async with aiofiles.open(path, "r", encoding="utf-8") as file:
                async for line in file:
                    if line.strip() == video.id:
                        return True

            return False
