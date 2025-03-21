"""The following is an example of how to use this library with multithreading."""

import time
from threading import Thread

from pyngrok import ngrok

from ytnoti import Video, YouTubeNotifier


def main() -> None:
    """Run the application."""
    ngrok.set_auth_token("Your ngrok token here")

    notifier = YouTubeNotifier()

    @notifier.any()
    async def listener1(video: Video) -> None:
        """Listener called when a video is uploaded or edited for any channel."""
        print("listener 1 called")
        print(video)

    notifier.subscribe("UCupvZG-5ko_eiXAupbDfxWw")
    thread = Thread(target=notifier.run)
    thread.start()

    # Simulate adding listener and subscriber after some time
    seconds = 10
    for i in range(seconds):
        print(f"Waiting for adding another listener in {seconds - i} seconds")
        time.sleep(1)

    print("Adding listener 2 and subscribing to another channel")

    async def listener2(video: Video) -> None:
        """Listener called when a video is uploaded or edited for any channel."""
        print("listener 2 called")
        print(video)

    notifier.add_any_listener(listener2)
    notifier.subscribe("UChLtXXpo4Ge1ReTEboVvTDg")

    try:
        thread.join()
    except KeyboardInterrupt:
        # Gracefully stop notifier
        notifier.stop()


if __name__ == "__main__":
    main()
