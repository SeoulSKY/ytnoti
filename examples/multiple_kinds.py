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

    @notifier.any()
    async def listener1(notification: Notification):
        """
        Listener called when a video is uploaded or updated
        """

        logger.info("listener 1 called")
        logger.info(notification)

    @notifier.upload()
    async def listener2(notification: Notification):
        """
        Listener called when a video on a specific channel is uploaded
        """

        logger.info("listener 2 called")
        logger.info(notification)

    @notifier.edit()
    async def listener3(notification: Notification):
        """
        Listener called when a video is edited on a specific channel
        """

        logger.info("listener 3 called")
        logger.info(notification)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    notifier.subscribe(["UCupvZG-5ko_eiXAupbDfxWw", "UChLtXXpo4Ge1ReTEboVvTDg"])
    notifier.run()


if __name__ == "__main__":
    main()
