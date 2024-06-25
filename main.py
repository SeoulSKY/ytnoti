import logging

from youtube_push_notification import YouTubePushNotifier, PushNotification

if __name__ == "__main__":
    channel_ids = ["UCFilzPS-na0PF1Gi5lQNDng", "UCupvZG-5ko_eiXAupbDfxWw", "UChLtXXpo4Ge1ReTEboVvTDg"]

    notifier = YouTubePushNotifier()

    @notifier.listener(channel_ids=channel_ids)
    async def listener(notification: PushNotification):
        print("listener called for channel: ", notification.channel.name)
        print(notification)


    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    notifier.run()
