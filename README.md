<div align="center">
    <img width="250" height="175" alt="logo" src="https://github.com/user-attachments/assets/14ed8fa6-7c2a-43dc-b9f4-05a54927c47d" />
    <h1>ytnoti</h1>
</div>

<blockquote align="center">
    Easy-to-use Python library for receiving real-time YouTube push notifications for video uploads, edits, deletions, and live streams.
</blockquote>

<!-- package -->
<div align="center">
    <img src="https://img.shields.io/pepy/dt/ytnoti" alt="Downloads">
    <img src="https://img.shields.io/github/license/SeoulSKY/ytnoti" alt="License">
    <a href="https://pypi.org/project/ytnoti"><img src="https://img.shields.io/pypi/v/ytnoti.svg?color=brightgreen&logo=pypi&logoColor=yellow" alt="PyPI version"></a>
    <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python" alt="Python versions">
    <a href="https://github.com/SeoulSKY/ytnoti/stargazers"><img src="https://img.shields.io/github/stars/SeoulSKY/ytnoti?logo=github" alt="GitHub stars"></a>
</div>
<!-- checks and tooling -->
<div align="center">
    <a href="https://codecov.io/github/SeoulSKY/ytnoti"><img src="https://codecov.io/github/SeoulSKY/ytnoti/graph/badge.svg?token=RYRIXW3LBO" alt="Coverage"></a>
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/pytest.yml/badge.svg" alt="pytest">
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/ruff.yml/badge.svg" alt="ruff">
    <img src="https://github.com/SeoulSKY/ytnoti/actions/workflows/ty.yml/badge.svg" alt="ty">
    <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv"></a>
</div>

<p align="center">
    <a href="https://ytnoti.readthedocs.io/en/latest/">Documentation</a>
    &nbsp;•&nbsp;
    <a href="https://ytnoti.readthedocs.io/en/latest/quickstart.html">Quickstart</a>
    &nbsp;•&nbsp;
    <a href="https://github.com/SeoulSKY/ytnoti/tree/main/examples">Examples</a>
    &nbsp;•&nbsp;
    <a href="https://ytnoti.readthedocs.io/en/latest/changelog.html">Changelog</a>
    &nbsp;•&nbsp;
    <a href="https://discord.gg/qvCdWEtqgB">Discord</a>
</p>

`ytnoti` is designed to help you receive YouTube push notifications in real-time for video
upload, edit, delete, and live stream easily and efficiently.

## ✨ Features

- **Real-time push, not polling** — YouTube's hub calls you the moment a video changes.
- **No API key, no quota** — nothing to provision, nothing to run out of.
- **Async and sync** — use `AsyncYouTubeNotifier`, or `YouTubeNotifier` if you don't run an event loop.
- **Listeners for every event** — `@notifier.upload()`, `@notifier.edit()`, `@notifier.delete()` and `@notifier.any()`, globally or per channel.
- **Brings its own server, or joins yours** — pass your existing `FastAPI` app and `ytnoti` mounts onto it.
- **Verified callbacks** — every notification is checked against an HMAC signature before a listener sees it.

## 🛠️ How it works

This library uses YouTube Data API v3 via [WebSub](https://www.w3.org/TR/websub/) (called
[PubSubHubbub](https://developers.google.com/youtube/v3/guides/push_notifications) in YouTube's docs) to
receive push notifications, so you can receive notifications in real time without constantly polling the YouTube API.

## 💻 Installation

This library requires `Python 3.11` or higher.

```bash
pip install ytnoti
```

## 📖 Simple Example

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

## 📚 Documentation

Please read the [documentation](https://ytnoti.readthedocs.io/en/latest/) before asking questions.
Your question may already be answered there.

## 👥 Community

If you are having any problems with using this library, please feel free to ask for help in the issues section or
on my Discord server.

<a href="https://discord.gg/qvCdWEtqgB">
    <img alt="discord invite" src="http://invidget.switchblade.xyz/qvCdWEtqgB">
</a>

## 🤝 Contributing

Contributions of every size are welcome — a bug report, a typo fix in the docs, or a new feature.
Read [CONTRIBUTING.md](https://github.com/SeoulSKY/ytnoti/blob/main/CONTRIBUTING.md) to set up the project with
[uv](https://docs.astral.sh/uv/) in a few commands, or browse the
[good first issues](https://github.com/SeoulSKY/ytnoti/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
to find somewhere to start.

### 🌟 Contributors

Thanks to everyone who has contributed to `ytnoti`!

<a href="https://github.com/SeoulSKY/ytnoti/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=SeoulSKY/ytnoti" alt="contributors" />
</a>

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/SeoulSKY/ytnoti/blob/main/LICENSE.md) file for details.
