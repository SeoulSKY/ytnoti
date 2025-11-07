"""Contains the tests for the class AsyncYouTubeNotifier."""

import asyncio
from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import PropertyMock, patch

import pytest
import respx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from tests import CALLBACK_URL
from ytnoti import AsyncYouTubeNotifier, Video

channel_ids = [
    "UCPF-oYb2-xN5FbCXy0167Gg",
    "UCuFFtHWoLl5fauMMD5Ww2jA",
    "UCupvZG-5ko_eiXAupbDfxWw",
]

channel_id = channel_ids[0]

CHANNEL_ID_VERIFICATION_URL = "https://www.youtube.com/feeds/videos.xml"
REGISTRATION_URL = "https://pubsubhubbub.appspot.com"

# ruff: noqa: E501 ERA001

xmls = [
    f"""
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
      <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
      <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"/>
      <title>YouTube video feed</title>
      <updated>2015-04-01T19:05:24.552394234+00:00</updated>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>{channel_id}</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/{channel_id}</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
    </feed>
    """,
    f"""
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
      <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
      <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"/>
      <title>YouTube video feed</title>
      <updated>2015-04-01T19:05:24.552394234+00:00</updated>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>{channel_id}</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/{channel_id}</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
    </feed>
    """,
    f"""
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
      <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
      <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"/>
      <title>YouTube video feed</title>
      <updated>2015-04-01T19:05:24.552394234+00:00</updated>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>{channel_id}</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/{channel_id}</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>{channel_id}</yt:channelId>
        <title>Video title</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/{channel_id}</uri>
        </author>
        <published>2015-03-06T21:40:57+00:00</published>
        <updated>2015-03-09T19:05:24.552394234+00:00</updated>
      </entry>
    </feed>
    """,
    f"""
    <feed xmlns:at="http://purl.org/atompub/tombstones/1.0" xmlns="http://www.w3.org/2005/Atom">
        <at:deleted-entry ref="yt:video:VIDEO_ID" when="2024-09-09T22:34:19.642702+00:00">
          <link href="https://www.youtube.com/watch?v=VIDEO_ID" />
          <at:by>
              <name>Channel title</name>
              <uri>https://www.youtube.com/channel/{channel_id}</uri>
          </at:by>
        </at:deleted-entry>
    </feed>
    """,
]

# ruff: enable


@pytest.fixture
def notifier() -> AsyncYouTubeNotifier:
    """Fixture for AsyncYouTubeNotifier."""
    notifier = AsyncYouTubeNotifier(callback_url=CALLBACK_URL)
    notifier._password = ""

    router = notifier._get_router()
    notifier._app.include_router(router)

    return notifier


@pytest.mark.asyncio
async def test_run() -> None:
    """Test run method."""
    notifier = AsyncYouTubeNotifier(callback_url=CALLBACK_URL)

    task = asyncio.create_task(notifier.run())

    await asyncio.sleep(2)

    try:
        assert notifier.is_ready
    finally:
        notifier.stop()
        await task


@pytest.mark.asyncio
async def test_run_in_background() -> None:
    """Test run_in_background method."""
    notifier = AsyncYouTubeNotifier(callback_url=CALLBACK_URL)

    async with notifier.run_in_background() as task:
        await asyncio.sleep(2)
        try:
            assert notifier.is_ready
        finally:
            notifier.stop()
            await task


def test_callback_url() -> None:
    """Test the callback URL configuration."""
    notifier = AsyncYouTubeNotifier(callback_url=CALLBACK_URL)
    assert notifier.callback_url is not None


@respx.mock
@pytest.mark.asyncio
async def test_subscribe() -> None:
    """Test the subscribe method of the YouTubeNotifier class."""
    notifier = AsyncYouTubeNotifier()

    respx.head(CHANNEL_ID_VERIFICATION_URL)
    route = respx.post(REGISTRATION_URL)
    route.mock(Response(HTTPStatus.NO_CONTENT))

    await notifier.subscribe(channel_ids)

    assert route.call_count == 0, "Should not subscribe before running the notifier"

    route.reset()

    notifier = AsyncYouTubeNotifier()

    type(notifier).is_ready = PropertyMock(return_value=True)
    await notifier.subscribe(channel_ids)

    assert route.call_count == len(channel_ids), "Should subscribe to each channel ID"

    route.reset()

    respx.head(CHANNEL_ID_VERIFICATION_URL).mock(Response(HTTPStatus.NOT_FOUND))
    with pytest.raises(ValueError):
        await notifier.subscribe("Invalid")

    assert not route.called, "Should not subscribe when the given channel ID is invalid"


@respx.mock
@pytest.mark.asyncio
async def test_unsubscribe(notifier: AsyncYouTubeNotifier) -> None:
    """Test the unsubscribe method of the YouTubeNotifier class."""
    respx.head(CHANNEL_ID_VERIFICATION_URL)
    route = respx.post(REGISTRATION_URL)
    route.mock(Response(HTTPStatus.NO_CONTENT))

    type(notifier).is_ready = PropertyMock(return_value=True)

    notifier._subscribed_ids.update(channel_ids)
    await notifier.unsubscribe(channel_ids)

    assert route.call_count == len(channel_ids), (
        "Should unsubscribe from each channel ID"
    )
    assert len(notifier._subscribed_ids) == 0, "Should remove unsubscribed channel IDs"

    route.reset()

    respx.head(CHANNEL_ID_VERIFICATION_URL).mock(Response(HTTPStatus.NOT_FOUND))

    with pytest.raises(ValueError):
        await notifier.unsubscribe("Invalid")

    assert not route.called, (
        "Should not unsubscribe when the given channel ID is invalid"
    )

    route.reset()

    respx.head(CHANNEL_ID_VERIFICATION_URL)

    notifier = AsyncYouTubeNotifier()
    with pytest.raises(ValueError):
        await notifier.unsubscribe(channel_ids)


def test_listener(notifier: AsyncYouTubeNotifier) -> None:
    """Test the upload decorator of the YouTubeNotifier class."""
    notifier._subscribed_ids.update(channel_ids)

    client = TestClient(notifier._app)
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

    response = client.post(CALLBACK_URL, content=content)
    assert response.status_code == HTTPStatus.NO_CONTENT

    assert any_called
    assert upload_called

    upload_called = False
    edit_called = False

    @notifier.edit()
    async def listener(_video: Video) -> None:
        nonlocal edit_called
        edit_called = True

    response = client.post(CALLBACK_URL, content=content)
    assert response.status_code == HTTPStatus.NO_CONTENT

    assert any_called
    assert edit_called
    assert not upload_called


def test_listener_channel_id(notifier: AsyncYouTubeNotifier) -> None:
    """Test the listener decorator with channel ID."""
    notifier._subscribed_ids.update(channel_ids)

    client = TestClient(notifier._app)
    content = xmls[0]

    called = 0

    @notifier.any(channel_ids=channel_id)
    async def listener(_video: Video) -> None:
        nonlocal called
        called += 1

    @notifier.any(channel_ids=[channel_id, "invalid"])
    async def listener(_video: Video) -> None:
        nonlocal called
        called += 1

    @notifier.any(channel_ids=["invalid"])
    async def listener(_video: Video) -> None:
        nonlocal called
        called += 1

    client.post(CALLBACK_URL, content=content)
    assert called == 2


def test_add_listener() -> None:
    """Test adding listeners to the YouTubeNotifier class."""
    notifier = AsyncYouTubeNotifier()

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


def test_get_server() -> None:
    """Test getting the server of the YouTubeNotifier class."""
    notifier = AsyncYouTubeNotifier()

    host = "0.0.0.0"  # noqa: S104
    port = 8000
    app = FastAPI()

    using_ngrok = notifier._using_ngrok
    notifier._using_ngrok = False
    notifier._get_server(host=host, port=port, app=app)

    app.get("/")(lambda: None)

    with pytest.raises(ValueError):
        notifier._get_server(host=host, port=port, app=app)

    notifier._using_ngrok = using_ngrok


@respx.mock
@pytest.mark.asyncio
async def test_verify_channel_ids() -> None:
    """Test verifying channel IDs."""
    respx.head(CHANNEL_ID_VERIFICATION_URL)
    notifier = AsyncYouTubeNotifier()
    await notifier._verify_channel_ids(channel_ids)

    respx.head(CHANNEL_ID_VERIFICATION_URL).mock(Response(HTTPStatus.NOT_FOUND))
    with pytest.raises(ValueError):
        await notifier._verify_channel_ids(["Invalid"])


def test_get(notifier: AsyncYouTubeNotifier) -> None:
    """Test the get method of the YouTubeNotifier class."""
    client = TestClient(notifier._app)

    response = client.get(CALLBACK_URL)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = client.get(CALLBACK_URL, params={"hub.challenge": 1})
    assert response.status_code == HTTPStatus.OK


def test_parse_timestamp(notifier: AsyncYouTubeNotifier) -> None:
    """Test parsing timestamp."""
    timestamp = "2015-04-01T19:05:24.552394234+00:00"
    parsed_timestamp = notifier._parse_timestamp(timestamp)
    assert parsed_timestamp == datetime(2015, 4, 1, 19, 5, 24, tzinfo=UTC)


def test_post(notifier: AsyncYouTubeNotifier) -> None:
    """Test the post method of the YouTubeNotifier class."""
    notifier._subscribed_ids.update(channel_ids)
    client = TestClient(notifier._app)

    headers = {"Content-Type": "application/xml"}
    for xml in xmls:
        response = client.post(CALLBACK_URL, headers=headers, content=xml)
        assert response.status_code == HTTPStatus.NO_CONTENT

    response = client.post(CALLBACK_URL, headers=headers, content="Invalid")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    with pytest.raises(RuntimeError):
        client.post(CALLBACK_URL, headers=headers, content="<feed/>")

    notifier._subscribed_ids.clear()
    with patch.object(notifier, "unsubscribe") as mock_unsubscribe:
        response = client.post(CALLBACK_URL, headers=headers, content=xmls[0])
        assert response.status_code == HTTPStatus.NO_CONTENT
        mock_unsubscribe.assert_awaited()

    password = notifier._password
    notifier._password = "password"  # noqa: S105
    response = client.post(CALLBACK_URL, headers=headers, content=xmls[0])
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    response = client.post(
        CALLBACK_URL,
        headers={**headers, "X-Hub-Signature": "sha256=password"},
        content=xmls[0],
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    notifier._password = password


@pytest.mark.asyncio
async def test_repeat_task(notifier: AsyncYouTubeNotifier) -> None:
    """Test repeat method of the YouTubeNotifier class."""
    timeout = 2
    started = datetime.now(UTC)

    called = 0

    async def task() -> None:
        nonlocal called
        called += 1

    await notifier._repeat_task(
        task, 1, lambda: (datetime.now(UTC) - started).total_seconds() < timeout
    )

    assert timeout - 1 <= called <= timeout

    called = 0

    async def task_exception() -> None:
        nonlocal called
        called += 1
        raise RuntimeError("Test exception")

    await notifier._repeat_task(task_exception, 0.1, lambda: called < 3)

    assert called == 3
