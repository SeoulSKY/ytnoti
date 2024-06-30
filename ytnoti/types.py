"""
This module contains type hints for the library.
"""

from typing import Callable, Coroutine, Any, TypeVar

from ytnoti.models.video import Video

NotificationListener = Callable[[Video], Coroutine[Any, Any, Any]]

T = TypeVar("T")
