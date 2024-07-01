"""
Example of a simple YouTube Notifier with logging module
"""


import logging

from pyngrok import ngrok

from ytnoti import YouTubeNotifier, Video


def main():
    """
    Main function
    """

    ngrok.set_auth_token("Your ngrok token here")

    logger = logging.getLogger(__name__)
    notifier = YouTubeNotifier()

    @notifier.upload()
    async def listener(video: Video):
        """
        Listener called when a video is uploaded or edited for any channel
        """

        logger.info("New video from %s: %s", video.channel.name, video.title)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
    notifier.run()


if __name__ == "__main__":
    main()
