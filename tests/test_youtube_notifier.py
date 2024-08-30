"""Contains the tests for the YouTube notifier class."""
from datetime import UTC, datetime
from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests import CALLBACK_URL, get_video, notifier  # noqa: F401
from ytnoti import Video, YouTubeNotifier

channel_ids = [
    "UCPF-oYb2-xN5FbCXy0167Gg",
    "UC9EEyg7QBL-stRX-7hTV3ng",
    "UCupvZG-5ko_eiXAupbDfxWw",
]

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
]


def test_callback_url(notifier: YouTubeNotifier) -> None:
    """Test the callback URL configuration."""
    assert notifier.callback_url is not None


def test_subscribe(notifier: YouTubeNotifier) -> None:
    """Test the subscribe method of the YouTubeNotifier class."""
    notifier.subscribe(channel_ids)

    with pytest.raises(ValueError):
        notifier.subscribe("Invalid")

    notifier = YouTubeNotifier()
    notifier.subscribe(channel_ids)
    assert len(notifier._subscribed_ids) == len(channel_ids)


def test_listener(notifier: YouTubeNotifier) -> None:
    """Test the upload decorator of the YouTubeNotifier class."""
    client = TestClient(notifier._config.app)
    content = xmls[0]
    any_called = False
    upload_called = False

    @notifier.any()
    async def listener(_video: Video) -> None:
        nonlocal any_called
        any_called = True

    @notifier.upload()
    async def listener(_video: Video) -> None:
        nonlocal upload_called
        upload_called = True

    client.post(CALLBACK_URL, content=content)

    assert any_called
    assert upload_called

    upload_called = False
    edit_called = False

    @notifier.edit()
    async def listener(_video: Video) -> None:
        nonlocal edit_called
        edit_called = True

    client.post(CALLBACK_URL, content=content)

    assert any_called
    assert edit_called
    assert not upload_called


def test_listener_channel_id(notifier: YouTubeNotifier) -> None:
    """Test the listener decorator with channel ID."""
    client = TestClient(notifier._config.app)
    content = xmls[0]

    called = 0

    @notifier.any(channel_ids="CHANNEL_ID")
    async def listener(_video: Video) -> None:
        nonlocal called
        called += 1

    @notifier.any(channel_ids=["CHANNEL_ID", "invalid"])
    async def listener(_video: Video) -> None:
        nonlocal called
        called += 1

    @notifier.any(channel_ids=["invalid"])
    async def listener(_video: Video) -> None:
        nonlocal called
        called += 1

    client.post(CALLBACK_URL, content=content)
    assert called == 2


def test_add_listener(notifier: YouTubeNotifier) -> None:
    """Test adding listeners to the YouTubeNotifier class."""

    async def listener1(_video: Video) -> None:
        pass

    async def listener2(_video: Video) -> None:
        pass

    async def listener3(_video: Video) -> None:
        pass

    notifier.add_any_listener(listener1)
    notifier.add_upload_listener(listener2)
    notifier.add_edit_listener(listener3)

    assert len(notifier._listeners) == 3

    with pytest.raises(ValueError):
        notifier.add_any_listener(listener1, channel_ids=notifier._ALL_LISTENER_KEY)


def test_get_server(notifier: YouTubeNotifier) -> None:
    """Test getting the server of the YouTubeNotifier class."""
    host = "0.0.0.0"  # noqa: S104
    port = 8000
    app = FastAPI()

    notifier._get_server(host=host, port=port, app=app)

    app.get("/")(lambda: None)

    with pytest.raises(ValueError):
        notifier._get_server(host=host, port=port, app=app)


def test_get(notifier: YouTubeNotifier) -> None:
    """Test the get method of the YouTubeNotifier class."""
    client = TestClient(notifier._config.app)

    response = client.get(CALLBACK_URL)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.get(CALLBACK_URL, params={"hub.challenge": 1})
    assert response.status_code == HTTPStatus.OK


def test_parse_timestamp(notifier: YouTubeNotifier) -> None:
    """Test parsing timestamp."""
    timestamp = "2015-04-01T19:05:24.552394234+00:00"
    parsed_timestamp = notifier._parse_timestamp(timestamp)
    assert parsed_timestamp == datetime(2015, 4, 1, 19, 5, 24, tzinfo=UTC)


def test_post(notifier: YouTubeNotifier) -> None:
    """Test the post method of the YouTubeNotifier class."""
    client = TestClient(notifier._config.app)

    headers = {"Content-Type": "application/xml"}
    for xml in xmls:
        response = client.post(CALLBACK_URL, headers=headers, content=xml)
        assert response.status_code == HTTPStatus.NO_CONTENT

    response = client.post(CALLBACK_URL, headers=headers, content="Invalid")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.post(CALLBACK_URL, headers=headers, content="<feed/>")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    notifier._config.password = "password"  # noqa: S105
    response = client.post(CALLBACK_URL, headers=headers, content=xmls[0])
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.post(CALLBACK_URL, headers={
        **headers, "X-Hub-Signature": "sha256=password"
    }, content=xmls[0])
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    notifier._config.password = ""
