.. ytnoti documentation master file, created by
   sphinx-quickstart on Wed Jun 26 19:28:55 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ytnoti
-------

.. image:: https://img.shields.io/badge/Python-v3.11-blue?logo=python
   :target: https://www.python.org/downloads/release/python-3110/
   :alt: Python version

.. image:: https://badge.fury.io/py/ytnoti.svg
    :target: https://badge.fury.io/py/ytnoti
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/dm/ytnoti
    :target: https://pypi.org/project/ytnoti/
    :alt: PyPI downloads

ytnoti is designed to help you receive YouTube push notifications for video
upload and edit in an easy and efficient way.

🛠️ How it works
----------------

This library uses YouTube Data API v3 via
`PubSubHubbub <https://developers.google.com/youtube/v3/guides/push_notifications>`_ to receive push
notifications, so you can receive notifications in real-time without constantly polling the YouTube API.

In addition, this method doesn't require any API key, so you can use this library **without any quota limit**.

💻 Installation
------------------

This library requires `Python 3.11` or higher.

.. code:: bash

   pip install ytnoti


📝 Simple Example
------------------

For more examples, please visit the `examples <https://github.com/SeoulSKY/ytnoti/tree/main/examples>`_ folder.

.. code:: python

   from ytnoti import YouTubeNotifier, Notification

   notifier = YouTubeNotifier()

   @notifier.upload()
   async def listener(notification: Notification):
       print(f"New video from {notification.channel.name}: {notification.video.title}")

   notifier.subscribe("UC9EEyg7QBL-stRX-7hTV3ng")  # Channel ID of SpeedyStyle
   notifier.run()

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
   :maxdepth: 3
   :caption: Contents:

   modules
   ytnoti
   ytnoti.models