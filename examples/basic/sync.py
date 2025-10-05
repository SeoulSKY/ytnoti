"""The following example demonstrates how to use the YouTubeNotifier to listen for
new video uploads from a channel.
"""

from pyngrok import ngrok

from ytnoti import Video, YouTubeNotifier


def main() -> None:
    """Run the application."""
    ngrok.set_auth_token("Your ngrok token here")

    notifier = YouTubeNotifier()

    @notifier.upload()
    async def listener(video: Video) -> None:
        print(f"New video from {video.channel.name}: {video.title}")

    notifier.subscribe("UCuFFtHWoLl5fauMMD5Ww2jA")  # Channel ID of CBC News
    notifier.run()


if __name__ == "__main__":
    main()
