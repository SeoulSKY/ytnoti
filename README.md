<div align="center">
    <h1>ytnoti</h1>
</div>

<blockquote align="center">
    An easy-to-use library for receiving YouTube push notification for video upload and update.
</blockquote>

<div align="center">
    <img src="https://img.shields.io/badge/Python-v3.11-blue">
    <img src="https://img.shields.io/github/license/SeoulSKY/SoruSora">
    <br>
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/pylint.yml/badge.svg">
    <br>
</div>

`ytnoti` is designed to help you receive YouTube push notifications for video
upload and update in an easy and efficient way.

# How it works

This library uses YouTube Data API v3 via 
[PubSubHubbub](https://developers.google.com/youtube/v3/guides/push_notifications) to receive push 
notifications, so you can receive notifications in real-time without constantly polling the YouTube API.

In addition, this method doesn't require any API key, so you can use this library **without any quota limit**.

# Installation

This library requires `Python 3.11` or higher.

```bash
pip install ytnoti
```

# Simple Example

For more examples, please visit the [examples](https://github.com/SeoulSKY/ytnoti/tree/main/examples) folder.

```python
from ytnoti import YouTubeNotifier, Notification

notifier = YouTubeNotifier()

@notifier.upload()
async def listener(notification: Notification):
    print(f"New video from {notification.channel.name}: {notification.video.title}")

notifier.subscribe(["UC9EEyg7QBL-stRX-7hTV3ng"])  # Channel ID of SpeedyStyle
notifier.run()
```

# Documentation

Read the [wiki](https://github.com/SeoulSKY/ytnoti/wiki) for more information.

# Community

If you have any questions about this library please visit my Discord server.

<a href="https://discord.gg/kQZDJJB">
    <img alt="discord invite" src="http://invidget.switchblade.xyz/kQZDJJB">
</a>

# License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/SeoulSKY/ytnoti/blob/main/LICENSE.md) file for details.
