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
However, you can pass your own FastAPI instance when you run (Async)YouTubeNotifier.

.. code:: python

    from fastapi import FastAPI
    from ytnoti import YouTubeNotifier

    app = FastAPI()

    # Do whatever you want with the app, like adding routes

    @app.get("/hello")
    async def hello():
        return {"message": "Hello World"}


    notifier = YouTubeNotifier()
    notifier.run(app=app)


Configuring uvicorn
-------------------

``(Async)YouTubeNotifier`` uses ``uvicorn`` to run the FastAPI server.
The library uses ``host`` 0.0.0.0 and ``port`` 8000 by default.
You can override them by passing them to the run (or serve) method.

.. code:: python

    notifier.run(host="123.456.789.012", port=5000)

For any keyword arguments that are passed to run (or serve) method,
it will directly be passed to the Config instance of ``uvicorn``.
See their `documentation <https://www.uvicorn.org/#usage>`_ for available options.

.. code:: python

    notifier.run(workers=3)
