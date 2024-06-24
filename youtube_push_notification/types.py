from typing import Callable, Coroutine, Any

from youtube_push_notification import PushNotification

PushNotificationListener = Callable[[PushNotification], Coroutine[Any, Any, None]]
