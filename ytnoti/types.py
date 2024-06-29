"""
This module contains type hints for the library.
"""

from typing import Callable, Coroutine, Any, TypeVar

from ytnoti.models.notification import Notification

PushNotificationListener = Callable[[Notification], Coroutine[Any, Any, Any]]

ReadyListener = Callable[[], Coroutine[Any, Any, Any]]

T = TypeVar("T")
