"""Contains type hints for the library."""

__all__ = [
    "AnyListener",
    "DeleteListener",
    "EditListener",
    "UploadListener",
]

from collections.abc import Awaitable, Callable

from ytnoti.models.video import DeletedVideo, Video

AnyListener = Callable[[Video | DeletedVideo], Awaitable[None]]
UploadListener = Callable[[Video], Awaitable[None]]
EditListener = Callable[[Video], Awaitable[None]]
DeleteListener = Callable[[DeletedVideo], Awaitable[None]]
