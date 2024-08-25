"""
This module contains the setup code that runs before the tests in this package.
"""

import os
import time
from threading import Thread

import pytest
from dotenv import load_dotenv
from pyngrok import ngrok

from ytnoti import YouTubeNotifier


CALLBACK_URL = "http://localhost:8000"

load_dotenv()
ngrok.set_auth_token(os.getenv("NGROK_TOKEN"))


@pytest.fixture(scope="session")
def notifier():
    """
    Setup/Teardown code that runs before and after the tests in this package.
    """

    noti = YouTubeNotifier()
    noti._config.password = ""
    thread = Thread(target=noti.run, name="notifier", daemon=True)
    thread.start()

    while True:
        if noti.is_ready:
            break

        time.sleep(0.1)

    yield noti
