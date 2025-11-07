"""Contains type hints for the library."""

from collections.abc import Awaitable, Callable
from typing import TypeVar

from ytnoti.models.video import Video

NotificationListener = Callable[[Video], Awaitable[None]]

T = TypeVar("T")
