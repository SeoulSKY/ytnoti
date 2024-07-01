Quick Start
===========

To get started, you need to install this package

.. code:: bash

    pip install ytnoti

.. note::
    Next step only applies to those who want to run the program in the local environment, not cloud environment with dedicated IP address.
    If you are going to pass ``callback_url`` to the ``(Async)YouTubeNotifier``, you can skip this step.

You need to signup for a free account at `here <https://dashboard.ngrok.com/get-started/setup>`_, and get your auth token

Then, before running your ``(Async)YouTubeNotifier``, add the following line:

.. code:: python

    from ytnoti import ngrok

    ngrok.set_auth_token("Your ngrok token here")

.. warning::
    Do not share your ngrok token with anyone. It can be used to access your ngrok account and expose your local network.
    Never commit your ngrok token to a public repository.

Following is the example code to get you started:

.. code:: python

    from pyngrok import ngrok
    from ytnoti import YouTubeNotifier, Video

    from ytnoti import ngrok

    ngrok.set_auth_token("Your ngrok token here")

    notifier = YouTubeNotifier()


    @notifier.upload()
    async def listener(video: Video):
        print(f"New video from {video.channel.name}: {video.title}")


    notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
    notifier.run()

``(Async)YouTubeNotifier`` also provides other decorator for your listener function:

- ``@notifier.any()``: Triggered when any event occurs
- ``@notifier.edit()``: Triggered when a video is edited

``any()``, ``upload()``, and ``edit()`` take an optional parameter ``channel_ids`` to only listen to events from specific channels.

.. code:: python

    @notifier.upload(channel_ids="UC9EEyg7QBL-stRX-7hTV3ng")
    async def listener(video: Video):
        print(f"New video from SpeedyStyle: {video.title}")

You can combine multiple decorators to listen to multiple events.
Following example listens to any channel's edit event and SpeedyStyle's upload event.

.. code:: python

    @notifier.edit()
    @notifier.upload(channel_ids="UC9EEyg7QBL-stRX-7hTV3ng")
    async def listener(video: Video):
        print(f"New video from SpeedyStyle: {video.title}")

Using callback_url
------------------

.. note::
    Following only applies when you run the program in the cloud environment with a dedicated IP address.

You can pass ``callback_url`` to the ``(Async)YouTubeNotifier`` to not use ngrok.
If your server IP is ``123.456.789.012`` and port is ``1234``, you can pass the following:

.. code:: python

    notifier = YouTubeNotifier(callback_url="http://123.456.789.012:1234")

Or your domain if you have one:

.. code:: python

    notifier = YouTubeNotifier(callback_url="http://yourdomain.com")

If you include endpoint in the URL, it will be used as the endpoint for the callback.

.. code:: python

    notifier = YouTubeNotifier(callback_url="http://yourdomain.com/endpoint")
