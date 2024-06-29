"""
This is an example of how to use decorators to listen to notifications.
"""


from ytnoti import YouTubeNotifier, Notification


def main():
    """
    Main function
    """

    notifier = YouTubeNotifier()

    @notifier.any()
    async def listener1(notification: Notification):
        """
        Listener called when a video is uploaded or edited for any channel
        """

        print("listener 1 called")
        print(notification)

    @notifier.upload()
    async def listener2(notification: Notification):
        """
        Listener called when a video is uploaded for any channel
        """

        print("listener 2 called")
        print(notification)

    @notifier.upload(channel_ids="UCupvZG-5ko_eiXAupbDfxWw")
    @notifier.edit()
    async def listener3(notification: Notification):
        """
        Listener called when a video is uploaded on a specific channel and when a video is edited on any channel
        """

        print("listener 3 called")
        print(notification)

    notifier.subscribe(["UCupvZG-5ko_eiXAupbDfxWw", "UChLtXXpo4Ge1ReTEboVvTDg"])
    notifier.run()


if __name__ == "__main__":
    main()
