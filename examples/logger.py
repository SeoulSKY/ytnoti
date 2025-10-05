"""THe following is an example of a simple YouTube Notifier with logging module."""

import logging

from pyngrok import ngrok

from ytnoti import Video, YouTubeNotifier


def main() -> None:
    """Run the application."""
    ngrok.set_auth_token("Your ngrok token here")

    logger = logging.getLogger(__name__)
    notifier = YouTubeNotifier()

    @notifier.upload()
    async def listener(video: Video) -> None:
        """Listener called when a video is uploaded or edited for any channel."""
        logger.info("New video from %s: %s", video.channel.name, video.title)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    notifier.subscribe("UCuFFtHWoLl5fauMMD5Ww2jA")  # Channel ID of CBC News
    notifier.run()


if __name__ == "__main__":
    main()
