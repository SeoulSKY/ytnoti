"""
This is a basic example of how to use the package to get notifications when a new video is uploaded or updated.
"""


import logging

from ytnoti import YouTubeNotifier, Notification


def main():
    """
    Main function
    """

    logger = logging.getLogger(__name__)
    notifier = YouTubeNotifier()

    @notifier.listener()
    async def my_listener(notification: Notification):
        """
        Listener called when a video is uploaded or updated
        """

        logger.info("listener called for channel: %s", notification.channel.name)
        logger.info(notification)

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    notifier.subscribe(["UCupvZG-5ko_eiXAupbDfxWw", "UChLtXXpo4Ge1ReTEboVvTDg"])
    notifier.run()


if __name__ == "__main__":
    main()
