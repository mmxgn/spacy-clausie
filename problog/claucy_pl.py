#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 13:38:38 2018

@author: Emmanouil Theofanis Chourdakis

Problog module for extracting information from a sentence using clausiepy

"""

from problog.extern import problog_export_nondet

import claucy as cl
import spacy

nlp = spacy.load("en")
cl.add_to_pipe(nlp)


@problog_export_nondet("+str", "-str", "-str", "-str")
def claucy(sent):
    """
        Extract triplets of the form: <predicate, arg1, arg2>
    """

    doc = nlp(sent)
    clauses = doc._.clauses

    result = []
    for clause in clauses:
        props = clause.to_propositions(as_text=False)
        for prop in props:
            if len(prop) == 3:
                result.append((str(prop[1]), str(prop[0]), str(prop[2])))

    return result
