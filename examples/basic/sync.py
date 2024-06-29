"""
This example demonstrates how to use the YouTubeNotifier to listen for new video uploads from a channel.
"""

from ytnoti import YouTubeNotifier, Notification


def main():
    """
    Main function
    """

    notifier = YouTubeNotifier()

    @notifier.upload()
    async def listener(notification: Notification):
        print(f"New video from {notification.channel.name}: {notification.video.title}")

    notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
    notifier.run()


if __name__ == "__main__":
    main()
