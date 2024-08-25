"""
This module contains the tests for the YouTube notifier class.
"""

from datetime import datetime, timezone
from http import HTTPStatus

import httpx
import pytest

from tests import notifier, CALLBACK_URL  # noqa: F401
from ytnoti import YouTubeNotifier


def test_subscribe_valid(notifier: YouTubeNotifier):
    """
    Test the subscribe method of the YouTubeNotifier class.
    """

    valid_channel_ids = ["UCPF-oYb2-xN5FbCXy0167Gg", "UC9EEyg7QBL-stRX-7hTV3ng", "UCupvZG-5ko_eiXAupbDfxWw"]
    notifier.subscribe(valid_channel_ids)


def test_subscribe_invalid(notifier: YouTubeNotifier):
    """
    Test the subscribe method of the YouTubeNotifier class with an invalid channel ID.
    """

    with pytest.raises(ValueError):
        notifier.subscribe("invalid_channel_id")

def test_get(notifier: YouTubeNotifier):
    """
    Test the get method of the YouTubeNotifier class.
    """

    response = httpx.get(CALLBACK_URL)
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = httpx.get(CALLBACK_URL, params={"hub.challenge": 1})
    assert response.status_code == HTTPStatus.OK


def test_parse_timestamp(notifier: YouTubeNotifier):
    """
    Test parsing timestamp
    """

    timestamp = "2015-04-01T19:05:24.552394234+00:00"
    parsed_timestamp = notifier._parse_timestamp(timestamp)
    assert parsed_timestamp == datetime(2015, 4, 1, 19, 5, 24, tzinfo=timezone.utc)


def test_post(notifier: YouTubeNotifier):
    """
    Test the post method of the YouTubeNotifier class.
    """

    headers = {
        "Content-Type": "application/xml"
    }

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
        response = httpx.post(CALLBACK_URL, headers=headers, content=xml)
        assert response.status_code == HTTPStatus.NO_CONTENT

    response = httpx.post(CALLBACK_URL, headers=headers, content="Invalid")
    assert response.status_code == HTTPStatus.BAD_REQUEST

    notifier._config.password = "password"
    response = httpx.post(CALLBACK_URL, headers=headers, content=xmls[0])
    assert response.status_code == HTTPStatus.UNAUTHORIZED
