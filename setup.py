#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

install_requires = []
with open("requirements.txt", "r") as infile:
    install_requires = [r for r in infile.read().split("\n") if r]

setup(
    name="pipoe",
    version="2019.10",
    description="Generate python bitbake recipes from pypi metadata.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NFJones/pipoe",
    author="Neil F Jones",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    keywords="yocto bitbake openembedded",
    packages=["pipoe"],
    python_requires="!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4",
    install_requires=install_requires,
    entry_points={"console_scripts": ["pipoe = pipoe.pipoe:main"]},
)
