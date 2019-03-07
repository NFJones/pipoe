#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="genpybb",
    version="2019.2",
    description="Generate python bitbake recipes from pypi metadata.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NFJones/genpybb",
    author="Neil F Jones",
    classifiers=[
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    keywords="yocto bitbake openembedded",
    packages=["genpybb"],
    python_requires="!=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4",
    entry_points={"console_scripts": ["genpybb = genpybb.genpybb:main"]},
)
