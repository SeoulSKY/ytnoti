<div align="center">
    <img width="250" height="175" alt="logo" src="https://github.com/user-attachments/assets/14ed8fa6-7c2a-43dc-b9f4-05a54927c47d" />
    <h1>ytnoti</h1>
</div>

<blockquote align="center">
    Easy-to-use Python library for receiving real-time YouTube push notifications for video uploads, edits, deletions, and live streams.
</blockquote>

<div align="center">
    <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python">
    <a href="https://pypi.org/project/ytnoti"><img src="https://img.shields.io/pypi/v/ytnoti.svg?color=brightgreen&logo=pypi&logoColor=yellow" alt="PyPI version"></a>
    <img src="https://img.shields.io/pepy/dt/ytnoti">
    <img src="https://img.shields.io/github/license/SeoulSKY/ytnoti">
</div>
<div align="center">
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/ruff.yml/badge.svg">
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/ty.yml/badge.svg">
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/pytest.yml/badge.svg">
    <a href="https://codecov.io/github/SeoulSKY/ytnoti">
        <img src="https://codecov.io/github/SeoulSKY/ytnoti/graph/badge.svg?token=RYRIXW3LBO"/>
    </a>
</div>

`ytnoti` is designed to help you receive YouTube push notifications in real-time for video
upload, edit, delete, and live stream easily and efficiently.

# 🛠️ How it works

This library uses YouTube Data API v3 via
[PubSubHubbub](https://developers.google.com/youtube/v3/guides/push_notifications) to receive push
notifications, so you can receive notifications in real time without constantly polling the YouTube API.

In addition, this method doesn't require any API key for YouTube Data API, so you can use this library **without any quota limit**.

# 💻 Installation

This library requires `Python 3.11` or higher.

```bash
pip install ytnoti
```

# 📖 Simple Example

Following is a simple example of how to use [ngrok](https://dashboard.ngrok.com/get-started/setup) to receive push notifications (not recommended for production).

```python
from pyngrok import ngrok
from ytnoti import YouTubeNotifier, Video

ngrok.set_auth_token("Your ngrok token here")

notifier = YouTubeNotifier()


@notifier.upload()
async def listener(video: Video) -> None:
    print(f"New video from {video.channel.name}: {video.title}")


notifier.subscribe("UCuFFtHWoLl5fauMMD5Ww2jA")  # Channel ID of CBC News
notifier.run()
```

Following is a simple example of how to use your domain to receive push notifications.

```python
from ytnoti import YouTubeNotifier, Video

notifier = YouTubeNotifier(callback_url="https://yourdomain.com")


@notifier.upload()
async def listener(video: Video) -> None:
    print(f"New video from {video.channel.name}: {video.title}")


notifier.subscribe("UCuFFtHWoLl5fauMMD5Ww2jA")  # Channel ID of CBC News
notifier.run()
```

For more examples, please visit the [examples](https://github.com/SeoulSKY/ytnoti/tree/main/examples) folder.

# 📚 Documentation

Please read the [documentation](https://ytnoti.readthedocs.io/en/latest/) before asking questions.
Your question may already be answered there.

# 👥 Community

If you are having any problems with using this library, please feel free to ask for help in the issues section or
on my Discord server.

<a href="https://discord.gg/qvCdWEtqgB">
    <img alt="discord invite" src="http://invidget.switchblade.xyz/qvCdWEtqgB">
</a>

# 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/SeoulSKY/ytnoti/blob/main/LICENSE.md) file for details.
