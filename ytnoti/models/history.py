"""
This module contains the video history model.
"""
import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from os import PathLike

from ytnoti.models.notification import Video


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

    def __init__(self, cache_size: int = 5000) -> None:
        """
        Create a new InMemoryVideoHistory instance.

        :param cache_size: The size of the cache. If the cache is full, the oldest video will be removed.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._video_ids: OrderedDict[str, None] = OrderedDict()
        self._cache_size = cache_size

    @property
    def cache_size(self) -> int:
        """
        Get the size of the cache.

        :return: The size of the cache.
        """

        return self._cache_size

    @cache_size.setter
    def cache_size(self, value: int) -> None:
        self._cache_size = value

    async def add(self, video: Video) -> None:
        self._logger.debug("Adding video (%s) to history", video.id)
        self._video_ids[video.id] = None

    async def has(self, video: Video) -> bool:
        return video.id in self._video_ids


class FileVideoHistory(VideoHistory):
    """
    Represents a file-based history of videos.
    """

    def __init__(self, path: PathLike[str]) -> None:
        """
        Create a new FileVideoHistory instance.

        :param path: The path to the file to store the history.
        """

        self._logger = logging.getLogger(self.__class__.__name__)
        self._path = path

    async def add(self, video: Video) -> None:
        with open(self._path, "a", encoding="utf-8") as file:
            self._logger.debug("Adding video (%s) to history", video.id)
            file.write(f"{video.id}\n")

    async def has(self, video: Video) -> bool:
        with open(self._path, "r", encoding="utf-8") as file:
            for line in file:
                if line.strip() == video.id:
                    return True

        return False
