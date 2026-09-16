"""Contains the tests for the class AsyncYouTubeNotifier."""

import asyncio
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from unittest.mock import PropertyMock, patch

import pytest
import respx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ConnectError, ReadTimeout, Request, Response

from tests import CALLBACK_URL
from ytnoti import AsyncYouTubeNotifier
from ytnoti.errors import HTTPError
from ytnoti.models.video import Channel, DeletedVideo, Timestamp, Video

channel_ids = [
    "UCPF-oYb2-xN5FbCXy0167Gg",
    "UCuFFtHWoLl5fauMMD5Ww2jA",
    "UCupvZG-5ko_eiXAupbDfxWw",
]

channel_id = channel_ids[0]

CHANNEL_ID_VERIFICATION_URL = "https://www.youtube.com/feeds/videos.xml"
REQUEST_URL = "https://pubsubhubbub.appspot.com"

# ruff: noqa: E501

published_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")

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
        <published>{published_at}</published>
        <updated>{published_at}</updated>
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
        <published>{published_at}</published>
        <updated>{published_at}</updated>
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
        <published>{published_at}</published>
        <updated>{published_at}</updated>
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
        <published>{published_at}</published>
        <updated>{published_at}</updated>
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


def get_feed(*, published: datetime, updated: datetime, title: str) -> str:
    """Create the body of a push notification for a video.

    :param published: The time the video was published.
    :param updated: The time the entry of the video was last updated.
    :param title: The title of the video.
    :return: The XML body of the notification.
    """
    fmt = "%Y-%m-%dT%H:%M:%S+00:00"

    return f"""
    <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
      <link rel="hub" href="https://pubsubhubbub.appspot.com"/>
      <link rel="self" href="https://www.youtube.com/xml/feeds/videos.xml?channel_id={channel_id}"/>
      <title>YouTube video feed</title>
      <updated>{updated.strftime(fmt)}</updated>
      <entry>
        <id>yt:video:VIDEO_ID</id>
        <yt:videoId>VIDEO_ID</yt:videoId>
        <yt:channelId>{channel_id}</yt:channelId>
        <title>{title}</title>
        <link rel="alternate" href="http://www.youtube.com/watch?v=VIDEO_ID"/>
        <author>
         <name>Channel title</name>
         <uri>http://www.youtube.com/channel/{channel_id}</uri>
        </author>
        <published>{published.strftime(fmt)}</published>
        <updated>{updated.strftime(fmt)}</updated>
      </entry>
    </feed>
    """


@pytest.fixture
def notifier() -> AsyncYouTubeNotifier:
    """Fixture for AsyncYouTubeNotifier."""
    app = FastAPI()
    notifier = AsyncYouTubeNotifier(callback_url=CALLBACK_URL, app=app)
    notifier._password = ""

    notifier._set_app_routes(app=app, callback_url=CALLBACK_URL)

    return notifier


@pytest.mark.asyncio
async def test_run() -> None:
    """Test run method."""
    notifier = AsyncYouTubeNotifier(callback_url=CALLBACK_URL)
    task = asyncio.create_task(notifier.run())

    await asyncio.sleep(1)

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
    """Test the subscribe method of the AsyncYouTubeNotifier class."""
    notifier = AsyncYouTubeNotifier()

    respx.head(CHANNEL_ID_VERIFICATION_URL)
    route = respx.post(REQUEST_URL)
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
    """Test the unsubscribe method of the AsyncYouTubeNotifier class."""
    respx.head(CHANNEL_ID_VERIFICATION_URL)
    route = respx.post(REQUEST_URL)
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


def test_listener(
    notifier: AsyncYouTubeNotifier,
) -> None:
    """Test the upload decorator of the AsyncYouTubeNotifier class."""
    notifier._subscribed_ids.update(channel_ids)

    client = TestClient(notifier._app)
    content = xmls[0]
    any_called = False
    upload_called = False

    @notifier.any()
    async def listener(_video: Video | DeletedVideo) -> None:
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

    any_called = False
    delete_called = False

    @notifier.delete()
    async def listener(_video: DeletedVideo) -> None:
        nonlocal delete_called
        delete_called = True

    response = client.post(
        CALLBACK_URL,
        content=f"""
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
    )
    assert response.status_code == HTTPStatus.NO_CONTENT

    assert any_called
    assert delete_called
    assert not upload_called


def test_listener_channel_id(notifier: AsyncYouTubeNotifier) -> None:
    """Test the listener decorator with channel ID."""
    notifier._subscribed_ids.update(channel_ids)

    client = TestClient(notifier._app)
    content = xmls[0]

    called = 0

    @notifier.any(channel_ids=channel_id)
    async def listener(_video: Video | DeletedVideo) -> None:
        nonlocal called
        called += 1

    @notifier.any(channel_ids=[channel_id, "invalid"])
    async def listener(_video: Video | DeletedVideo) -> None:
        nonlocal called
        called += 1

    @notifier.any(channel_ids=["invalid"])
    async def listener(_video: Video | DeletedVideo) -> None:
        nonlocal called
        called += 1

    client.post(CALLBACK_URL, content=content)
    assert called == 2


def test_add_listener() -> None:
    """Test adding listeners to the AsyncYouTubeNotifier class."""
    notifier = AsyncYouTubeNotifier()

    async def listener1(_video: Video | DeletedVideo) -> None:
        pass

    async def listener2(_video: Video) -> None:
        pass

    async def listener3(_video: Video) -> None:
        pass

    async def listener4(_video: DeletedVideo) -> None:
        pass

    notifier.add_any_listener(listener1)
    notifier.add_upload_listener(listener2)
    notifier.add_edit_listener(listener3)
    notifier.add_delete_listener(listener4)

    assert len(notifier._any_listeners) == 1
    assert len(notifier._upload_listeners) == 1
    assert len(notifier._edit_listeners) == 1
    assert len(notifier._delete_listeners) == 1

    with pytest.raises(ValueError):
        notifier.add_any_listener(listener1, channel_ids=notifier._ALL_LISTENER_KEY)


def test_endpoint() -> None:
    """Test setting up the notifier."""
    assert (
        AsyncYouTubeNotifier._get_endpoint(callback_url="http://localhost:8000") == "/"
    )
    assert (
        AsyncYouTubeNotifier._get_endpoint(callback_url="http://localhost:8000/test")
        == "/test"
    )


def test_verify_app() -> None:
    """Test setting up the notifier."""
    app = FastAPI()

    AsyncYouTubeNotifier._verify_app(app=app, callback_url=CALLBACK_URL)

    @app.get("/")
    async def root() -> None:
        pass

    with pytest.raises(ValueError):
        AsyncYouTubeNotifier._verify_app(app=app, callback_url=CALLBACK_URL)


@respx.mock
@pytest.mark.asyncio
async def test_on_startup(notifier: AsyncYouTubeNotifier) -> None:
    """Test the on_start event handler of the AsyncYouTubeNotifier class."""
    route = respx.head(CALLBACK_URL)

    route.mock(Response(HTTPStatus.OK))

    with patch.object(notifier, "_repeat_task"):
        await notifier._on_startup(callback_url=CALLBACK_URL)
        assert notifier._server_ready_event.is_set()

        route.mock(side_effect=ConnectError)

        called = 0

        def predicate() -> bool:
            nonlocal called

            if called >= 3:
                route.mock(Response(HTTPStatus.OK))
                return False

            called += 1
            return True

        await notifier._on_startup(callback_url=CALLBACK_URL, predicate=predicate)
        assert notifier._server_ready_event.is_set()


@respx.mock
@pytest.mark.asyncio
async def test_on_startup_defers_the_first_request(
    notifier: AsyncYouTubeNotifier,
) -> None:
    """Test that the on_start event handler makes the first request in the
    repeated task, so that a failure of it is retried.
    """
    respx.head(CALLBACK_URL).mock(Response(HTTPStatus.OK))
    route = respx.post(REQUEST_URL).mock(Response(HTTPStatus.SERVICE_UNAVAILABLE))
    notifier._subscribed_ids.update(channel_ids)

    with patch.object(notifier, "_repeat_task") as repeat_task:
        await notifier._on_startup(callback_url=CALLBACK_URL)

    assert not route.called

    task = repeat_task.call_args.args[0]
    with pytest.raises(HTTPError):
        await task()

    assert route.call_count == len(channel_ids)


def test_setup_notifier(notifier: AsyncYouTubeNotifier) -> None:
    """Test setting up the notifier."""
    with patch("pyngrok.ngrok.connect") as mock_connect:
        mock_connect.return_value.public_url = "test"

        notifier._setup_notifier(app=notifier._app, port=8000, callback_url=None)
        assert notifier._callback_url == "test"

        mock_connect.return_value.public_url = None

        with pytest.raises(RuntimeError):
            notifier._setup_notifier(app=notifier._app, port=8000, callback_url=None)


def test_stop(notifier: AsyncYouTubeNotifier) -> None:
    """Test stopping the notifier."""
    type(notifier).is_ready = PropertyMock(return_value=True)
    notifier._is_using_ngrok = True

    with (
        patch.object(notifier, "_server") as mock_server,
        patch("pyngrok.ngrok.disconnect") as mock_disconnect,
    ):
        notifier.stop()

        assert mock_server.should_exit
        assert notifier._server is None

        mock_disconnect.assert_called_once_with(notifier._callback_url)


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
    """Test the get method of the AsyncYouTubeNotifier class."""
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


@respx.mock
@pytest.mark.asyncio
async def test_request(notifier: AsyncYouTubeNotifier) -> None:
    """Test the request method of the AsyncYouTubeNotifier class."""
    route = respx.post(REQUEST_URL)

    route.mock(Response(HTTPStatus.NO_CONTENT))
    await notifier._request([channel_id])

    route.mock(Response(HTTPStatus.BAD_REQUEST))
    with pytest.raises(HTTPError):
        await notifier._request([channel_id])

    type(notifier).is_ready = PropertyMock(return_value=False)
    route.mock(Response(HTTPStatus.CONFLICT))
    with pytest.raises(ConnectionError):
        await notifier._request([channel_id])

    type(notifier).is_ready = PropertyMock(return_value=True)
    with pytest.raises(HTTPError):
        await notifier._request([channel_id])


@respx.mock
@pytest.mark.asyncio
async def test_request_continues_after_failure(
    notifier: AsyncYouTubeNotifier,
) -> None:
    """Test that the request method requests every channel even if some fail."""
    requested = []

    def side_effect(request: Request) -> Response:
        requested.append(request)
        if len(requested) == 1:
            raise ReadTimeout("Timed out", request=request)
        return Response(HTTPStatus.NO_CONTENT)

    respx.post(REQUEST_URL).mock(side_effect=side_effect)

    with pytest.raises(ReadTimeout):
        await notifier._request(channel_ids)

    assert len(requested) == len(channel_ids)


def test_get_delay() -> None:
    """Test the delay between the repeated runs of a task."""
    interval = timedelta(days=1)

    assert AsyncYouTubeNotifier._get_delay(interval, 0) == interval
    assert (
        AsyncYouTubeNotifier._get_delay(interval, 1)
        == AsyncYouTubeNotifier._RETRY_INITIAL_INTERVAL
    )
    assert (
        AsyncYouTubeNotifier._get_delay(interval, 2)
        == AsyncYouTubeNotifier._RETRY_INITIAL_INTERVAL * 2
    )

    # The backoff never exceeds the interval, no matter how many failures
    assert AsyncYouTubeNotifier._get_delay(interval, 1000) == interval
    assert AsyncYouTubeNotifier._get_delay(timedelta(seconds=1), 5) == timedelta(
        seconds=1
    )


def test_post(notifier: AsyncYouTubeNotifier) -> None:
    """Test the post method of the AsyncYouTubeNotifier class."""
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
    with patch.object(notifier, "_request") as mock_request:
        response = client.post(CALLBACK_URL, headers=headers, content=xmls[0])
        assert response.status_code == HTTPStatus.NO_CONTENT
        mock_request.assert_awaited()

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


def test_classify(notifier: AsyncYouTubeNotifier) -> None:
    """Test the classify method of the AsyncYouTubeNotifier class."""
    published = datetime.now(UTC)

    channel = Channel(
        id="CHANNEL_ID",
        name="Channel title",
        url="http://www.youtube.com/channel/CHANNEL_ID",
    )

    video = Video(
        id="VIDEO_ID",
        title="Video title",
        url="http://www.youtube.com/watch?v=VIDEO_ID",
        timestamp=Timestamp(published=published, updated=published),
        channel=channel,
    )

    assert notifier._classify(video, in_history=False) == "upload"

    # YouTube keeps moving the updated timestamp away from the published one
    # while it settles a new video, which says nothing about it being an edit.
    video.timestamp.updated = published + timedelta(minutes=8)
    assert notifier._classify(video, in_history=False) == "upload"

    # Every notification after the first one is an edit.
    assert notifier._classify(video, in_history=True) == "edit"

    # A video the history has never seen is an edit if it is too old to have
    # just been uploaded, since the history cannot reach back far enough.
    old = Video(
        id="OLD_VIDEO_ID",
        title="Old video title",
        url="http://www.youtube.com/watch?v=OLD_VIDEO_ID",
        timestamp=Timestamp(
            published=published
            - AsyncYouTubeNotifier._UPLOAD_PUBLISHED_THRESHOLD
            - timedelta(seconds=1),
            updated=published,
        ),
        channel=channel,
    )

    assert notifier._classify(old, in_history=False) == "edit"


def test_post_classifies_the_first_notification_as_an_upload(
    notifier: AsyncYouTubeNotifier,
) -> None:
    """Test that a new video is an upload however late YouTube updated it."""
    notifier._subscribed_ids.add(channel_id)

    uploads: list[Video] = []
    edits: list[Video] = []

    @notifier.upload()
    async def listener(video: Video) -> None:
        uploads.append(video)

    @notifier.edit()
    async def listener(video: Video) -> None:
        edits.append(video)

    # The hub sent the same new video four times, the last two of them after
    # its title had been edited.
    published = datetime.now(UTC)
    notifications = [
        (timedelta(minutes=2), "Video title"),
        (timedelta(minutes=5), "Video title"),
        (timedelta(minutes=16), "Edited video title"),
        (timedelta(minutes=16), "Edited video title"),
    ]

    client = TestClient(notifier._app)
    with patch.object(
        notifier._video_history, "add", wraps=notifier._video_history.add
    ) as mock_add:
        for delay, title in notifications:
            response = client.post(
                CALLBACK_URL,
                headers={"Content-Type": "application/xml"},
                content=get_feed(
                    published=published, updated=published + delay, title=title
                ),
            )
            assert response.status_code == HTTPStatus.NO_CONTENT

        # The video is recorded once, however many times the hub resends it, so
        # a history that evicts its oldest entries keeps holding as many videos.
        mock_add.assert_awaited_once()

    assert len(uploads) == 1
    assert len(edits) == len(notifications) - 1


@pytest.mark.asyncio
async def test_repeat_task(notifier: AsyncYouTubeNotifier) -> None:
    """Test repeat method of the AsyncYouTubeNotifier class."""
    timeout = 2
    started = datetime.now(UTC)

    called = 0

    async def task() -> None:
        nonlocal called
        called += 1

    await notifier._repeat_task(
        task,
        timedelta(seconds=1),
        lambda: (datetime.now(UTC) - started).total_seconds() < timeout,
    )

    assert timeout - 1 <= called <= timeout

    called = 0

    async def task_exception() -> None:
        nonlocal called
        called += 1
        raise RuntimeError("Test exception")

    await notifier._repeat_task(
        task_exception, timedelta(seconds=0.1), lambda: called < 3
    )

    assert called == 3
