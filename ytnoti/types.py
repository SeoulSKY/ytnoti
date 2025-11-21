"""Contains type hints for the library."""

__all__ = [
    "AnyListener",
    "EditListener",
    "UploadListener",
]

from collections.abc import Awaitable, Callable

from ytnoti.models.video import Video

AnyListener = Callable[[Video], Awaitable[None]]
UploadListener = Callable[[Video], Awaitable[None]]
EditListener = Callable[[Video], Awaitable[None]]
