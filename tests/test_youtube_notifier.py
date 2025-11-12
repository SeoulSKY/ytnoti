"""Contains the tests for the class YouTubeNotifier."""

import time
from threading import Thread
from unittest.mock import patch

import pytest
from fastapi import FastAPI

from tests import CALLBACK_URL
from ytnoti import AsyncYouTubeNotifier, YouTubeNotifier

channel_ids = [
    "UCPF-oYb2-xN5FbCXy0167Gg",
    "UCuFFtHWoLl5fauMMD5Ww2jA",
    "UCupvZG-5ko_eiXAupbDfxWw",
]

# ruff: noqa: E501 ERA001

xmls = [
    """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
      <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
      <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id=CHANNEL_ID"/>
      <title>YouTube video feed</title>
      <updated>2015-04-01T19:05:24.552394234+00:00</updated>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>CHANNEL_ID</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/CHANNEL_ID</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
    </feed>
    """,
    """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
      <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
      <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id=CHANNEL_ID"/>
      <title>YouTube video feed</title>
      <updated>2015-04-01T19:05:24.552394234+00:00</updated>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>CHANNEL_ID</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/CHANNEL_ID</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
    </feed>
    """,
    """
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
      <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
      <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id=CHANNEL_ID"/>
      <title>YouTube video feed</title>
      <updated>2015-04-01T19:05:24.552394234+00:00</updated>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>CHANNEL_ID</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/CHANNEL_ID</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>CHANNEL_ID</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/CHANNEL_ID</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
    </feed>
    """,
    """
    <feed xmlns:at="http://purl.org/atompub/tombstones/1.0" xmlns="http://www.w3.org/2005/Atom">
        <at:deleted-entry ref="yt:video:VIDEO_ID" when="2024-09-09T22:34:19.642702+00:00">
            <link href="https://www.youtube.com/watch?v=VIDEO_ID" />
            <at:by>
                <name>Channel title</name>
                <uri>https://www.youtube.com/channel/CHANNEL_ID</uri>
            </at:by>
        </at:deleted-entry>
    </feed>
    """,
]

# ruff: enable


@pytest.fixture
def notifier() -> YouTubeNotifier:
    """Fixture for YouTubeNotifier."""
    app = FastAPI()
    notifier = YouTubeNotifier(app=app, callback_url=CALLBACK_URL)
    notifier._password = ""

    notifier._set_app_routes(app=app, callback_url=CALLBACK_URL)

    return notifier


def test_run() -> None:
    """Test run method of the YouTubeNotifier class."""
    notifier = YouTubeNotifier(callback_url=CALLBACK_URL)

    thread = Thread(target=notifier.run)
    thread.start()

    time.sleep(2)

    try:
        assert notifier.is_ready
    finally:
        notifier.stop()
        thread.join()


def test_run_in_background() -> None:
    """Test run_in_background method of the YouTubeNotifier class."""
    notifier = YouTubeNotifier(callback_url=CALLBACK_URL)

    with notifier.run_in_background():
        time.sleep(2)

        assert notifier.is_ready


def test_subscribe(notifier: YouTubeNotifier) -> None:
    """Test subscribe method of the YouTubeNotifier class."""
    with patch.object(AsyncYouTubeNotifier, "subscribe") as mock_subscribe:
        notifier.subscribe(channel_ids)
        mock_subscribe.assert_awaited_with(channel_ids)


def test_unsubscribe(notifier: YouTubeNotifier) -> None:
    """Test unsubscribe method of the YouTubeNotifier class."""
    with patch.object(AsyncYouTubeNotifier, "unsubscribe") as mock_unsubscribe:
        notifier.unsubscribe(channel_ids)
        mock_unsubscribe.assert_awaited_with(channel_ids)
