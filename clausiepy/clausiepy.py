#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 25 17:57:27 2018

@author: Emmanouil Theofanis Chourdakis <e.t.chourdakis@qmul.ac.uk>

Reimplementation in spacy+python of:
    
Del Corro Luciano, and Rainer Gemulla. 
"Clausie: clause-based open information extraction." 
Proceedings of the 22nd international conference on World Wide Web. ACM, 2013.

"""

import os
dirpath = os.path.dirname(os.path.realpath(__file__))

# Load NLP model
import spacy
from spacy import displacy
nlp = spacy.load('en')

# Dictionaries
dict_non_ext_copular = ['die', 'walk']
dict_ext_copular = ['act',
                    'appear',
                    'be',
                    'become',
                    'come',
                    'come out',
                    'end up',
                    'get',
                    'go',
                    'grow',
                    'fall',
                    'feel',
                    'keep',
                    'leave',
                    'look',
                    'prove',
                    'remain',
                    'seem',
                    'smell',
                    'sound',
                    'stay',
                    'taste',
                    'turn',
                    'turn up',
                    'wind up',
                    'live',
                    'come',
                    'go',
                    'stand',
                    'lie',
                    'love',
                    'do',
                    'try']

dict_copular = ['act',
                'appear',
                'be',
                'become',
                'come',
                'come out',
                'end up',
                'get',
                'go',
                'grow',
                'fall',
                'feel',
                'keep',
                'leave',
                'look',
                'prove',
                'remain',
                'seem',
                'smell',
                'sound',
                'stay',
                'taste',
                'turn',
                'turn up',
                'wind up']

dict_complex_transitive = ['bring',
                           'catch',
                           'drive',
                           'get',
                           'keep',
                           'lay',
                           'lead',
                           'place',
                           'put',
                           'set',
                           'sit',
                           'show',
                           'stand',
                           'slip',
                           'take']


dict_ignore = ['so', 'then', 'thus', 'why', 'as', 'even']   


def translate_clause(clause):
    """ Modifies clause so that relative clause indicators (whose, which, where)
        are resolved before subsequent processing 
    """
    
    for n, token in enumerate(clause['S']):
        # If you have a "which" or a "whose", replace it with the token pointed
        # by the relcl dependency of the antidescendant.
        
        if token.text.lower() in ['which', 'who']:
            if token.head.dep_ == 'relcl':
                clause['S'].remove(token)
                clause['S'].insert(0, token.head.head)
                
    if 'A' in clause:
        for n, token in enumerate(clause['A']):        
            if token.text.lower() in ['where']:
                if token.head.dep_ == 'relcl':
                    clause['A'].remove(token)
                    clause['A'].insert(0, token.head.head.head)        
                
    if 'A?' in clause:
        for n, token in enumerate(clause['A?']):        
            if token.text.lower() in ['where']:
                if token.head.dep_ == 'relcl':
                    clause['A?'].remove(token)
                    clause['A?'].insert(0, token.head.head.head)               

    return clause


def empty_clause():
    return  {'S':[], 'V':[], 'O':[], 'IO': [], 'XCOMP': [], 'A':[], 'C':[]}

def has_object(clause):
    return has_dobj(clause) or has_iobj(clause)

def has_dobj(clause):
    return len(clause['O']) > 0

def has_iobj(clause):
    return len(clause['IO']) > 0

def has_complement(clause):
    return len(clause['C']) > 0 or len(clause['XCOMP']) > 0

def has_candidate_adverbial(clause):
    for verb in clause['V']:
        for adv in clause['A']:
            if adv in verb.subtree and adv.i > verb.i:
                return True
            
    else:
        return False
    
def has_known_non_ext_copular(clause):
    for verb in clause['V']:
        if nlp(verb.text)[0].lemma_ in dict_non_ext_copular:
            return True
    else:
        return False
    
def has_known_ext_copular(clause):
    for verb in clause['V']:
        if nlp(verb.text)[0].lemma_ in dict_ext_copular:
            return True
    else:
        return False        
    
def is_known_ext_copular(verb):
    return nlp(verb.text)[0].lemma_ in dict_ext_copular

    
def is_known_copular(verb):
    return str(verb) in dict_copular
    
def has_potentially_complex_transitive(clause):
    for verb in clause['V']:
        if nlp(verb.text)[0].lemma_ in dict_complex_transitive:
            return True
    else:
        return False          
    
def is_in_ignore_list(adverb):
    return nlp(adverb.text)[0].lemma_ in dict_ignore

def clausie(sent, conservative=True):
    
    def process_dependants(token, clause):
        dependants = [c for c in token.head.subtree if c not in token.subtree]
        for d in dependants:
            if d.dep_ in ['dobj']:
                clause['O'].append(d)
            elif d.dep_ in  ['iobj', 'dative']:
                clause['IO'].append(d)
            elif d.dep_ in ['ccomp', 'acomp', 'attr']:
                clause['C'].append(d)
                    
            elif d.dep_ in ['xcomp']:
                if is_known_copular(d):
                    clause['XCOMP'].append(d.head)
                else:
                    clause['O'].append(d)
            elif d.dep_ in ['advmod', 'advcl', 'npadvmod']:
                clause['A'].append(d)
            elif d.dep_ in ['oprd'] and d.head in clause['V']:
                clause['A'].append(d)
            elif d.dep_ in ['prep']:
                # Capture "prep_in(X, Y)".
                # which is prep(X, in) and pobj(in, Y)
                for c in d.children:
                    if c.dep_ == 'pobj':
                       # clause['A'].append(c)        
                        clause['A'].append(d)
    
    doc = nlp(sent)
    clauses = []
    
    clause = empty_clause()
    
    # Check if root is not a verb
    root = [t for t in doc if t.dep_ == 'ROOT'][0]
    if root.pos_ != 'VERB':
        doc = nlp("There is " + sent)
    
    # Subjects of a verb
    for token in doc:
      #  print("{}({},{})".format(token.dep_, token.head, token))
        if token.dep_ in ['nsubj', 'nsubjpass', 'attr']:
            clause['S'].append(token)
            clause['V'].append(token.head)
            
            # Take dependants: 
            process_dependants(token, clause)

            clauses.append(translate_clause(clause))
            clause = empty_clause()
            
        elif token.dep_ in ['csubj']:
            clause['S'].append(token)
            clause['V'].append(token.head)
            
            # Take dependants: 
            dependants = [c for c in token.head.subtree if c not in token.subtree]
            #dependants = token.head.children
            for d in dependants:
                if d.dep_ in ['dobj']:
                    clause['O'].append(d)           

            clauses.append(translate_clause(clause))
            clause = empty_clause()
        elif token.dep_ in ['appos']:
            # Subjects without a verb
            # E.g. Sam is my brother in: Sam, my brother. 
            clause['S'].append(token.head)
            clause['V'].append(nlp('is')[0])
            clause['C'].append(token)
            clauses.append(translate_clause(clause))
            clause = empty_clause()
        elif token.dep_ in ['poss']:
            # Subjects declaring possesion
            # E.g. my brother: in: Sam, my brother.
            toktext = token.text
            if token.text.lower() == 'his':
                clause['S'].append(nlp('he')[0])
                clause['V'].append(nlp('has')[0])
            elif token.text.lower() == 'her':
                clause['S'].append(nlp('she')[0])
                clause['V'].append(nlp('has')[0])
            elif token.text.lower() == 'my':
                clause['S'].append(nlp('I')[0])
                clause['V'].append(nlp('have')[0])
            elif token.text.lower() == 'its':
                clause['S'].append(nlp('it')[0])
                clause['V'].append(nlp('has')[0])
            elif token.text.lower() == 'our':
                clause['S'].append(nlp('we')[0])
                clause['V'].append(nlp('have')[0])
            elif token.text.lower() == 'your':
                clause['S'].append(nlp('you')[0])
                clause['V'].append(nlp('have')[0])     
            elif token.text.lower() == 'their':
                clause['S'].append(nlp('they')[0])
                clause['V'].append(nlp('have')[0])  
            else:
                clause['S'].append(token)
                clause['V'].append(nlp('has')[0])
            clause['O'].append(token.head)
            clauses.append(translate_clause(clause))
            clause = empty_clause()
        elif token.dep_ in ['acl']:
            # Create a synthetic from participial modifiers (partmod).
            clause['S'].append(token.head)
            new_sent = nlp("are {}".format(" ".join([t.text for t in token.subtree])))
            r = [t for t in new_sent if t.dep_ == 'ROOT'][0]
            clause['V'].append(r)
            
            process_dependants(token, clause)
            
            
            clauses.append(translate_clause(clause))
            clause = empty_clause()

    # Identify clause types
    for clause in clauses:
        type_ = 'OTHER'
        if not has_object(clause): # Q1
            if has_complement(clause):  #Q2
                type_ = 'SVC'
            else:
                # Q3
                if not has_candidate_adverbial(clause):
                    type_ = 'SV'
                else:
                    # Q4
                    if has_known_non_ext_copular(clause):
                        type_ = 'SV'
                    else:
                        # Q5
                        if has_known_ext_copular(clause):
                            type_ = 'SVA'
                        else:
                            # Q6: Cases we want conservative or non-conservative estimation
                            if conservative:
                                type_ = 'SVA'
                            else:
                                type_ = 'SV'
                                    
        else:
            # Q7
            if has_dobj(clause) and has_iobj(clause):
                type_ = 'SVOO'
            else:
                # Q8
                if has_complement(clause):
                    type_ = 'SVOC'
                else:
                    #Q9
                    if not has_candidate_adverbial(clause) and has_dobj(clause):
                        type_ = 'SVO'
                    else:
                        # Q10
                        if has_potentially_complex_transitive(clause):
                            type_ = 'SVOA'
                        else: 
                            # Q11
                            if conservative:
                                type_ = 'SVOA'
                            else:
                                type_ = 'SVO'        
                                
        clause['type'] = type_
        
        if type_ in ['SVC', 'SVOO', 'SVOC', 'SV', 'SVO']:
            clause['A?'] = clause['A']
            clause.pop('A', None)
    
    return clauses

def append_conjugates(L):
    for l in L:
        if type(l) == str:
            continue
        for c in l.children:
            if c.dep_ in ['conj']:
                L.append(c)
                
def extract_propositions(clauses):
    propositions = []    
    for clause in clauses:

        subjects = clause['S']
        append_conjugates(subjects)

        verbs = clause['V']
        append_conjugates(verbs)

        type_ = clause['type']

        for s in subjects:
            for v in verbs:
                
                if type(v) == str:
                    v = nlp(v)[0]
                
                prop = (s, v)

                if type_ in ['SV']:
                    if prop not in propositions:
                        if v.text in ['is' ,'are']:
                            propositions.append({'subject':s, 'verb':nlp("exists")[0]})
                        else:
                            propositions.append({'subject': s,  'verb':v})
                        
                        
                    adverbs = clause['A?']
                    append_conjugates(adverbs)
                    for a in adverbs:
                        if not is_in_ignore_list(a):
                            prop =  {'subject': s,  'verb':v, 'adverb':a}
                            if prop not in propositions:
                                propositions.append(prop)
                elif type_ in ['SVO']:
                    objects = clause['O']
                    append_conjugates(objects)
                    adverbs = clause['A?']
                    append_conjugates(adverbs)
                    
                    for o in objects:
                        
                        
                        prop = {'subject': s,  'verb':v, 'direct object':o}
                        if prop not in propositions:
                            propositions.append(prop)
                        for a in adverbs:
                            if not is_in_ignore_list(a):
                                prop = {'subject': s,  'verb':v, 'direct object':o, 'adverb':a}
                                if prop not in propositions:
                                    propositions.append(prop)                                
                                    
                        # Extractions of form: 
                        # AE had a faboulous hairstyle -> Hairstyle was faboulous
                        for c in o.children:
                            if c.dep_ == 'amod':
                                prop = {'subject': o, 'verb':[t for t in nlp('is')][0], 'complement':c}
                                if prop not in propositions:
                                    propositions.append(prop)

                                    
                elif type_ in ['SVA']:
                    adverbs = clause['A']
                    append_conjugates(adverbs)
                    for a in adverbs:
                        if not is_in_ignore_list(a):
                            prop =  {'subject': s,  'verb':v, 'adverb':a}
                            if prop not in propositions:
                                propositions.append(prop)           
                elif type_ in ['SVC']:
                    comp = clause['C']
                    adverbs = clause['A?']
                    append_conjugates(adverbs)
                    append_conjugates(comp)
                    for c in comp:
                        prop =  {'subject': s,  'verb':v, 'complement':c}
                        if prop not in propositions:
                            propositions.append(prop) 
                        for a in adverbs:
                            if not is_in_ignore_list(a):
                                prop = {'subject': s,  'verb':v, 'complement':c, 'adverb':a}
                                if prop not in propositions:
                                    propositions.append(prop)                            
                elif type_ in ['SVOO']:
                    dobjects = clause['O']
                    iobjects = clause['IO']

                    append_conjugates(dobjects)
                    append_conjugates(iobjects)
                    adverbs = clause['A?']
                    append_conjugates(adverbs)

                    for io in iobjects:
                        for do in dobjects:
                            prop = {'subject': s,  'verb':v, 'indirect object':io, 'direct object':do}
                            if prop not in propositions:
                                propositions.append(prop)    
                                
                            for a in adverbs:
                                if not is_in_ignore_list(a):
                                    for do in dobjects:
                                        prop = {'subject': s,  'verb':v, 'indirect object':io, 'direct object':do, 'adverb': a}
                                        if prop not in propositions:
                                            propositions.append(prop)                                     

                elif type_ in ['SVOA']:
                    dobjects = clause['O']
                    append_conjugates(dobjects)
                    adverbs = clause['A']
                    append_conjugates(adverbs)

                    for a in adverbs:
                        if not is_in_ignore_list(a):
                            for do in dobjects:
                                prop = {'subject': s,  'verb':v,  'direct object':do, 'adverb': a}
                                if prop not in propositions:
                                    propositions.append(prop)       
                elif type_ in ['SVOC']:
                    dobjects = clause['O']
                    append_conjugates(dobjects)

                    comp = clause['C']
                    append_conjugates(comp)
                    
                    adverbs = clause['A?']
                    append_conjugates(adverbs)                    

                    for c in comp:
                        for do in dobjects:
                            prop = {'subject': s,  'verb':v,  'direct object':do, 'complement': c}
                            
                            if prop not in propositions:
                                propositions.append(prop) 
                                
                            for a in adverbs:
                                if not is_in_ignore_list(a):
                                    for do in dobjects:
                                        prop = {'subject': s, 'verb':v,  'direct object':do, 'complement':c, 'adverb': a}
                                        if prop not in propositions:
                                            propositions.append(prop)                                      
    return propositions
            
def get_conj_text(token):
    L = [token]
    token_old = None
    while token_old != token:
        token_old = token
        for c in token.children:
            if c.dep_ in ['cc', 'punct']:
                L.append(c)
            if c.dep_ == 'conj':
                L.append(c)
                token = c
                break
                
    return " ".join([t.text for t in L])
            
def proposition_text(prop):       
    
   # subject = [t for t in prop['subject'].children if t.dep_ in ['det', 'amod']]  + [prop['subject']]
    subject = [t for t in prop['subject'].lefts] + [prop['subject']]
    
    # Add of the
    for t in prop['subject'].rights:
        if t.dep_ in ['prep']:
            subject += [d for d in t.subtree]
        
        
    
    if 'indirect object' in prop:
        indirect_object = [t for t in prop['indirect object'].children if t.dep_ in ['det', 'amod', 'compound']] + [prop['indirect object']]
    else:
        indirect_object = []
        
    if 'direct object' in prop:
        direct_object = [t for t in prop['direct object'].children if t.dep_ in ['det', 'amod', 'compound']] + [prop['direct object']]
    else:
        direct_object = []
        
    if 'complement' in prop:
        complement = [t for t in prop['complement'].subtree]
    else:
        complement = []
        
    if 'adverb' in prop:
        adv = prop['adverb']
        if adv.dep_ == 'pobj' and adv.head.dep_ =='prep':
            # Prepositional phrase
            adverb = [adv.head] + [t for t in prop['adverb'].subtree]
        elif adv.dep_ == 'advmod' and adv.head.dep_ == 'npadvmod':
            adverb = [t for t in adv.head.subtree]
        else:
            adverb = [t for t in prop['adverb'].subtree]
    else:
        adverb = []
        
    verb_aux = [p for p in prop['verb'].lefts if p.dep_ in ['aux', 'auxpass']]
    verb = verb_aux+[prop['verb']]
    
    return subject , verb , indirect_object , direct_object , complement , adverb

def proposition_text_str(prop):
    """ Like proposition_text(prop) but returns a string isntead """
    L = proposition_text(prop)
    
    str_list = []
    
    for l in L:
        if len(l)>0:
            str_list += l
            
    return " ".join([t.text for t in str_list]) + " ."

def print_propositions(plist):
    for prop in plist:
        text = proposition_text(prop)
        print(text)

if __name__ == "__main__":
    
    from util import *
    
    print("Testing with various sentences")
    sentences = [
            "Bell , a telecommunication company based in Los Angeles , makes and distributes electronic , computer and building products",
            "AE died.",
            "AE remained in Princeton.",
            "AE is smart.",
            "AE has won the Nobel Prize.",
            "RSAS gave AE the Nobel Prize.",
            "The doorman showed AE to his office .",
            "AE declared the meeting open .",
            "AE died in Princeton in 1955 .",
            "AE remained in Princeton until his death .",
            "AE is a scientist of the 20th century .",
            "AE has won the Nobel Prize in 1921 .",
            "In 1921, AE has won the Nobel Prize . ",
            "Nicolas Cage graciously ate and enjoyed the blue fruit and the yellow steak.",
            "A bull was feeding in a meadow until a lion approached the bull",
            "The attack of the lion caused the death of the bull.",
            "Some crows are eating rubbish at a garbage dump.",
            "AE knocked the door three times.",
            "All crows have a beak.",
            "AE had a faboulous hairstyle.",
            ]
    
    for sent in sentences:
        print("Sentence:")
        print(sent)
        print("Dependencies:")
        tree_from_doc(nlp(sent)).show()
        print("Clauses:")
        clauses = clausie(sent)
        print()
        for clause in clauses:
            print("\t{}".format(clause))
        print()
        print("Propositions:")
        propositions = extract_propositions(clauses)
        for prop in propositions:
            print(proposition_text_str(prop))
        #print_propositions(propositions)

        print("-----")

