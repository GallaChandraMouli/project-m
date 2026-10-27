from setuptools import setup, find_packages

setup(
    name="nexus-worker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.27.0",
        "websockets>=12.0",
        "click>=8.1.7",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "nexus-worker = nexus_worker.cli:cli",
        ],
    },
)
