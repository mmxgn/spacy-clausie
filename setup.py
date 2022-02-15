#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 25 18:21:51 2018

@author: Emmanouil Theofanis Chourdakis
"""

from setuptools import setup, find_packages
import unittest


setup(
    name="claucy",
    version="0.0.2.000",
    packages=find_packages(),
    # scripts=['claucy/__init__.py', 'clausiepy/__init__.py'],
    install_requires=["spacy>=3.0.0", "lemminflect>=0.2.1"],
    test_suite="tests.test_suite",
    author="Emmanouil Theofanis Chourdakis",
    author_email="etchourdakis@gmail.com",
    description="A reimplementation of ClausIE Information Extraction System in python",
    url="https://github.com/mmxgn/spacy-clausie",
    keywords="openie clausie information extraction spacy",
    include_package_data=True,
)
