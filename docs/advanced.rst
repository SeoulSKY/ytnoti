Advanced
========

Using Your Domain
------------------

You can pass ``callback_url`` to the ``(Async)YouTubeNotifier`` to use your own domain rather than ``ngrok``.
If your server IP is ``123.456.789.012``, you can pass the following:

.. code:: python

    notifier = YouTubeNotifier(callback_url="https://123.456.789.012")

Or your domain if you have one:

.. code:: python

    notifier = YouTubeNotifier(callback_url="https://yourdomain.com")

If you include endpoint in the URL, it will be used as the endpoint for the callback.

.. code:: python

    notifier = YouTubeNotifier(callback_url="https://yourdomain.com/endpoint")

Using Your FastAPI Instance
---------------------------

By default, ``(Async)YouTubeNotifier`` creates a new FastAPI instance internally.
However, you can pass your own FastAPI instance when you create (Async)YouTubeNotifier.

.. code:: python

    from fastapi import FastAPI
    from ytnoti import YouTubeNotifier

    app = FastAPI()

    # Do whatever you want with the app, like adding routes

    @app.get("/hello")
    async def hello():
        return {"message": "Hello World"}


    notifier = YouTubeNotifier(app=app)

    @notifier.upload()
    async def listener(video):
        print(f"New video from {video.channel.name}: {video.title}")


    notifier.subscribe("UCuFFtHWoLl5fauMMD5Ww2jA")  # Channel ID of CBC News
    notifier.run()


Configuring uvicorn
-------------------

``(Async)YouTubeNotifier`` uses ``uvicorn`` to run the FastAPI server.
The library uses ``host`` 0.0.0.0 and ``port`` 8000 by default.
You can override them by passing them to the run method.

.. code:: python

    notifier.run(host="123.456.789.012", port=5000)

For any keyword arguments that are passed to run method,
it will directly be passed to the Config instance of ``uvicorn``.
See their `documentation <https://www.uvicorn.org/#usage>`_ for available options.

.. code:: python

    notifier.run(workers=3)

Using Your Own Video History Class
----------------------------------

Since YouTube Data API doesn't provide information whether the notification is for upload or edit,
``(Async)YouTubeNotifier`` uses ``InMemoryVideoHistory`` by default to keep track of the video history.
If the video is not in the history, it will be considered as a new video.
Otherwise, it will be considered as an edited video.

The library provides ``FileVideoHistory`` class that saves the video history to files. To use it, pass it to the ``video_history`` parameter.

.. code:: python

    from ytnoti import YouTubeNotifier, FileVideoHistory

    notifier = YouTubeNotifier(video_history=FileVideoHistory(dir_path="video_history"))

You can also create your own video history class by inheriting ``VideoHistory`` and implementing
the abstract methods ``add`` and ``has``.

.. code:: python

    from ytnoti import YouTubeNotifier, Video, VideoHistory

    class MyVideoHistory(VideoHistory):
        async def add(self, video: Video) -> None:
            pass

        async def has(self, video: Video) -> bool:
            return False

    notifier = YouTubeNotifier(video_history=MyVideoHistory())
