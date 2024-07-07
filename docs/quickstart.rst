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

    from ytnoti import ngrok

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

    from ytnoti import ngrok

    ngrok.set_auth_token("Your ngrok token here")

    notifier = YouTubeNotifier()


    @notifier.upload()
    async def listener(video: Video):
        print(f"New video from {video.channel.name}: {video.title}")


    notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
    notifier.run()

Using Decorators
----------------

``(Async)YouTubeNotifier`` also provides following decorators for your listener function:

- ``@notifier.any()``: Triggered when any event occurs
- ``@notifier.edit()``: Triggered when a video is edited
- ``@notifier.upload()``: Triggered when a new video is uploaded

``any()``, ``edit()`` and ``upload()`` take an optional parameter ``channel_ids`` to only listen to events from specific channels.

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
