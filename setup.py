#! /usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="SECOS",
    version="0.1",
    author="Martin Riedl",
    author_email="riedlma@gmail.com",
    description="An unsupervised compound splitter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/riedlma/SECOS",
    license="Apache License 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Typing :: Typed",
    ],
    packages=setuptools.find_packages(include=['secos', 'secos.*']),
    python_requires=">=3.7",
    install_requires=["scipy"],
)
