from youtube_push_notification import YouTubePushNotifier, PushNotification

channel_ids = ["UCFilzPS-na0PF1Gi5lQNDng", "UCupvZG-5ko_eiXAupbDfxWw", "UChLtXXpo4Ge1ReTEboVvTDg"]

notifier = YouTubePushNotifier()


@notifier.listener()
async def listener(notification: PushNotification):
    print("listener called")
    print(notification)


if __name__ == "__main__":
    notifier.run(channel_ids)
