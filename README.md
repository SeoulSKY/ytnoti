<div align="center">
    <h1>ytnoti</h1>
</div>

<blockquote align="center">
    Easy-to-use Python library for receiving YouTube push notifications for video upload and edit
</blockquote>

<div align="center">
    <img src="https://img.shields.io/badge/Python-v3.11-blue?logo=python">
    <a href="https://pypi.org/project/ytnoti"><img src="https://img.shields.io/pypi/v/ytnoti.svg?color=brightgreen&logo=pypi&logoColor=yellow" alt="PyPI version"></a>
    <img src="https://img.shields.io/pypi/dm/ytnoti">
    <img src="https://img.shields.io/github/license/SeoulSKY/ytnoti">
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/pylint.yml/badge.svg">
</div>

`ytnoti` is designed to help you receive YouTube push notifications for video
upload and edit in an easy and efficient way.

# 🛠️ How it works

This library uses YouTube Data API v3 via 
[PubSubHubbub](https://developers.google.com/youtube/v3/guides/push_notifications) to receive push 
notifications, so you can receive notifications in real time without constantly polling the YouTube API.

In addition, this method doesn't require any API key, so you can use this library **without any quota limit**.

# 💻 Installation

This library requires `Python 3.11` or higher.

```bash
pip install ytnoti
```

# 📝 Simple Example

For more examples, please visit the [examples](https://github.com/SeoulSKY/ytnoti/tree/main/examples) folder.

```python
from ytnoti import YouTubeNotifier, Notification

notifier = YouTubeNotifier()

@notifier.upload()
async def listener(notification: Notification):
    print(f"New video from {notification.channel.name}: {notification.video.title}")

notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
notifier.run()
```

# 📚 Documentation

Please read the [documentation](https://ytnoti.readthedocs.io/en/latest/) before asking questions. 
Your question may already be answered there.

# 👥 Community

If you are having any problems with using this library, please feel free to ask for help in the issues section or 
on my Discord server.

<a href="https://discord.gg/kQZDJJB">
    <img alt="discord invite" src="http://invidget.switchblade.xyz/kQZDJJB">
</a>

# 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/SeoulSKY/ytnoti/blob/main/LICENSE.md) file for details.
