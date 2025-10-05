Quick Start
===========

To get started, you need to install this package

.. code:: bash

    pip install ytnoti

Using Ngrok
-----------

.. note::
    This step only applies to those who want to run the program without a dedicated IP address or domain. To use your domain, see the :doc:`advanced` section.

You need to signup for a free account at `here <https://dashboard.ngrok.com/get-started/setup>`_, and get your auth token

Then, before running your ``(Async)YouTubeNotifier``, add the following line:

.. code:: python

    from pyngrok import ngrok

    ngrok.set_auth_token("Your ngrok token here")

.. warning::
    Do not share your ngrok token with anyone. It can be used to access your ngrok account and expose your local network.
    Never commit your ngrok token to a public repository.

Example Usage
-------------

Following is the example code to get you started:

.. code:: python

    from pyngrok import ngrok
    from ytnoti import YouTubeNotifier, Video

    ngrok.set_auth_token("Your ngrok token here")

    notifier = YouTubeNotifier()


    @notifier.upload()
    async def listener(video: Video):
        print(f"New video from {video.channel.name}: {video.title}")


    notifier.subscribe("UCuFFtHWoLl5fauMMD5Ww2jA")  # Channel ID of CBC News
    notifier.run()

Using Decorators
----------------

``(Async)YouTubeNotifier`` provides following decorators for your listener function:

- ``@notifier.any()``: Triggered when any event occurs
- ``@notifier.edit()``: Triggered when a video is edited
- ``@notifier.upload()``: Triggered when a new video is uploaded

They take an optional parameter ``channel_ids`` to only listen to events from specific channels.

.. code:: python

    @notifier.upload(channel_ids="UCuFFtHWoLl5fauMMD5Ww2jA")
    async def listener(video: Video):
        print(f"New video from CBC News: {video.title}")

You can combine multiple decorators to listen to multiple events.
Following example listens to any channel's edit event and CBC News' upload event.

.. code:: python

    @notifier.edit()
    @notifier.upload(channel_ids="UCuFFtHWoLl5fauMMD5Ww2jA")
    async def listener(video: Video):
        print(f"New video from CBC News: {video.title}")
