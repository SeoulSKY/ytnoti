"""
Setup script for ytnoti
"""


from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as file:
    long_description = file.read()

setup(
    name="ytnoti",
    version="1.1.1",
    packages=find_packages(),
    author="SeoulSKY",
    author_email="contact@seoulsky.org",
    description="Easy-to-use python library for receiving YouTube push notification for video upload and edit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "fastapi~=0.111.0",
        "httpx~=0.27.0",
        "uvicorn~=0.30.1",
        "xmltodict~=0.13.0",
        "pyngrok~=7.1.6",
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
