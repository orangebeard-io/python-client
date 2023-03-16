from setuptools import setup, find_packages

__version__ = "0.0.1"


def file_contents(filename):
    with open(filename, "r") as fh:
        return fh.read()


setup(
    name="orangebeard-client",
    version=__version__,
    author="Team Soju",
    author_email="info@orangbeard.io",
    description="A python3 client for Orangebeard",
    long_description=file_contents("README.MD"),
    long_description_content_type="text/markdown",
    url="https://github.com/orangebeard-io/python-client",
    packages=find_packages(),
    install_requires=file_contents("requirements.txt").splitlines(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: AGPL :: 3",
        "Operating System :: OS Independent",
    ],
)
