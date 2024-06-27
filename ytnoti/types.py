"""
This module contains type hints for the library.

Types:
    PushNotificationListener
    ReadyListener
"""

from typing import Callable, Coroutine, Any

from ytnoti import Notification

PushNotificationListener = Callable[[Notification], Coroutine[Any, Any, Any]]

ReadyListener = Callable[[], Coroutine[Any, Any, Any]]
