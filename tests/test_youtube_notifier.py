"""Contains the tests for the YouTube notifier class."""

from datetime import UTC, datetime
from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from tests import CALLBACK_URL, notifier  # noqa: F401
from ytnoti import YouTubeNotifier


def test_subscribe(notifier: YouTubeNotifier) -> None:
    """Test the subscribe method of the YouTubeNotifier class."""
    channel_ids = [
        "UCPF-oYb2-xN5FbCXy0167Gg",
        "UC9EEyg7QBL-stRX-7hTV3ng",
        "UCupvZG-5ko_eiXAupbDfxWw",
    ]
    notifier.subscribe(channel_ids)

    with pytest.raises(ValueError):
        notifier.subscribe("Invalid")


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

    for xml in xmls:
        response = client.post(CALLBACK_URL, headers=headers, content=xml)
        assert response.status_code == HTTPStatus.NO_CONTENT

    response = client.post(CALLBACK_URL, headers=headers, content="Invalid")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    notifier._config.password = "password"  # noqa: S105
    response = client.post(CALLBACK_URL, headers=headers, content=xmls[0])
    notifier._config.password = ""
    assert response.status_code == HTTPStatus.UNAUTHORIZED
