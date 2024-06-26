"""
This is an example of how to use decorators to listen to notifications.
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
        Listener called when a video is uploaded or edited for any channel
        """

        logger.info("listener 1 called")
        logger.info(notification)

    @notifier.upload()
    async def listener2(notification: Notification):
        """
        Listener called when a video is uploaded for any channel
        """

        logger.info("listener 2 called")
        logger.info(notification)

    @notifier.upload(channel_ids="UCupvZG-5ko_eiXAupbDfxWw")
    @notifier.edit()
    async def listener3(notification: Notification):
        """
        Listener called when a video is uploaded on a specific channel and when a video is edited on any channel
        """

        logger.info("listener 3 called")
        logger.info(notification)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    notifier.subscribe(["UCupvZG-5ko_eiXAupbDfxWw", "UChLtXXpo4Ge1ReTEboVvTDg"])
    notifier.run()


if __name__ == "__main__":
    main()
