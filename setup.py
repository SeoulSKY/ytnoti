from setuptools import setup, find_packages

setup(
    name="youtube-push-notification",
    version="0.1.0",
    packages=find_packages(),
    author="SeoulSKY",
    author_email="contact@seoulsky.org",
    description="Youtube Push Notification",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=[
        "fastapi~=0.111.0",
        "requests~=2.32.3",
        "pyngrok~=7.1.6",
        "uvicorn~=0.30.1",
        "xmltodict~=0.13.0",
    ],
    url="https://github.com/SeoulSKY/youtube-push-notification",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
