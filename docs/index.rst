.. ytnoti documentation master file, created by
   sphinx-quickstart on Wed Jun 26 19:28:55 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ytnoti
-------

.. image:: https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python
   :target: https://www.python.org/downloads/release/python-3110/
   :alt: Python version

.. image:: https://img.shields.io/pypi/v/ytnoti.svg?color=brightgreen&logo=pypi&logoColor=yellow
    :target: https://pypi.org/project/ytnoti/
    :alt: PyPI version

.. image:: https://img.shields.io/pepy/dt/ytnoti
    :target: https://pypi.org/project/ytnoti/
    :alt: PyPI downloads

.. image:: https://img.shields.io/github/license/SeoulSKY/ytnoti
    :target: https://github.com/SeoulSKY/ytnoti/blob/main/LICENSE.md
    :alt: License

ytnoti is designed to help you receive YouTube push notifications for video
upload and edit in an easy and efficient way.

🛠️ How it works
----------------

This library uses YouTube Data API v3 via
`PubSubHubbub <https://developers.google.com/youtube/v3/guides/push_notifications>`_ to receive push
notifications, so you can receive notifications in real-time without constantly polling the YouTube API.

In addition, this method doesn't require any API key for YouTube Data API, so you can use this library **without any quota limit**.

💻 Installation
------------------

This library requires `Python 3.11` or higher.

.. code:: bash

   pip install ytnoti


📖 Simple Example
------------------

Following is a simple example of how to use `ngrok <https://dashboard.ngrok.com/get-started/setup>`_ to receive push notifications.

.. code:: python

   from pyngrok import ngrok
   from ytnoti import YouTubeNotifier, Video

   ngrok.set_auth_token("Your ngrok token here")

   notifier = YouTubeNotifier()


   @notifier.upload()
   async def listener(video: Video):
       print(f"New video from {video.channel.name}: {video.title}")


   notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
   notifier.run()

Following is a simple example of how to use your domain to receive push notifications.

.. code:: python

   from ytnoti import YouTubeNotifier, Video

   notifier = YouTubeNotifier(callback_url="https://yourdomain.com")


   @notifier.upload()
   async def listener(video: Video):
       print(f"New video from {video.channel.name}: {video.title}")


   notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
   notifier.run()


For more examples, please visit the `examples <https://github.com/SeoulSKY/ytnoti/tree/main/examples>`_ folder.

👥 Community
-------------

If you have any questions about this library please visit my Discord server.

.. image:: http://invidget.switchblade.xyz/kQZDJJB
   :target: https://discord.gg/kQZDJJB
   :alt: Discord server


📄 License
------------

This project is licensed under the MIT License - see the `LICENSE.md <https://github.com/SeoulSKY/ytnoti/blob/main/LICENSE.md>`_ file for details.

.. toctree::
    :hidden:
    :caption: Getting Started

    quickstart
    advanced

.. toctree::
    :hidden:
    :caption: Classes
    :glob:

    classes/*

.. toctree::
    :hidden:
    :caption: Data
    :glob:

    data/*

.. toctree::
    :hidden:
    :caption: Enums
    :glob:

    enums/*

.. toctree::
    :hidden:
    :caption: Errors
    :glob:

    errors/*

.. toctree::
    :hidden:
    :caption: More Information

    faq
    changelog
