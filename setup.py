"""Setup script for ytnoti."""

from pathlib import Path

from setuptools import find_packages, setup

with Path("README.md").open() as file:
    long_description = file.read()

setup(
    name="ytnoti",
    version="2.1.3",
    packages=find_packages(),
    author="SeoulSKY",
    author_email="contact@seoulsky.dev",
    description="Easy-to-use Python library for receiving YouTube push notification "
    "for video upload and edit in real-time",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "fastapi~=0.115.0",
        "httpx~=0.28.1",
        "uvicorn~=0.34.0",
        "xmltodict~=0.14.2",
        "pyngrok~=7.2.3",
        "aiofiles~=24.1.0",
    ],
    url="https://github.com/SeoulSKY/ytnoti",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
