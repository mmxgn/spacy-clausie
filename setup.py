#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 25 18:21:51 2018

@author: Emmanouil Theofanis Chourdakis
"""



from setuptools import setup, find_packages
setup(
    name="clausiepy",
    version="0.0.1",
    packages=find_packages(),
    #scripts=['clausiepy/clausiepy.py', 'clausiepy/__init__.py'],
    install_requires=['spacy>=2.0.0'],
    
    author="Emmanouil Theofanis Chourdakis",
    author_email="e.t.chourdakis@qmul.ac.uk", 
    description="A reimplementation of ClausIE Information Extraction System in python",
    url="https://github.com/mmxgn/clausiepy",
    keywords="openie clausie information extraction",
    include_package_data=True,
    
)
