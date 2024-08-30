"""Contains type hints for the library."""

from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from ytnoti.models.video import Video

NotificationListener = Callable[[Video], Coroutine[Any, Any, Any]]

T = TypeVar("T")
