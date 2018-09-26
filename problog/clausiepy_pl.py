#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 26 13:38:38 2018

@author: Emmanouil Theofanis Chourdakis

Problog module for extracting information from a sentence using clausiepy

"""

from problog.extern import problog_export_nondet

import clausiepy as cl

def remove_apostrophe(string):
    # Remove "'"S
    if string[0] == "'":
        string = string[1:]
    if string[-1] == "'":
        string = string[:-1]    
        
    return string

@problog_export_nondet('+str', '-str', '-str', '-str', '-str', '-str', '-str')
def clausie(sent):
    
    sent = remove_apostrophe(sent)
    
    clauses = cl.clausie(sent)
    
    propositions = cl.extract_propositions(clauses)    

    result = []
    for proposition in propositions:
        ptext = cl.proposition_text(proposition)
        
        prop = []
        
        for p in ptext:
            prop.append(" ".join([pp.text for pp in p]))
            
        result.append(tuple(prop))
        
    return result