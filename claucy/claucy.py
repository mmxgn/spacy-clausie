#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 18:07:24 2019

@author: Emmanouil Theofanis Chourdakis

Clausie as a spacy library
"""

import spacy
from spacy.tokens import Span, Doc
from spacy.matcher import Matcher

# DO NOT SET MANUALLY
MOD_CONSERVATIVE = False

Doc.set_extension("clauses", default=[], force=True)
Span.set_extension("clauses", default=[], force=True)

dictionary = {
    "non_ext_copular": """die walk""".split(),
    "ext_copular": """act
appear
be
become
come
come out
end up
get
go
grow
fall
feel
keep
leave
look
prove
remain
seem
smell
sound
stay
taste
turn
turn up
wind up
live
come
go
stand
lie
love
do
try""".split(),
    "complex_transitive": """
bring
catch
drive
get
keep
lay
lead
place
put
set
sit
show
stand
slip
take""".split(),
    "adverbs_ignore": """so
then
thus
why
as
even""".split(),
    "adverbs_include": """
hardly
barely
scarcely
seldom
rarely""".split(),
}


class Clause:
    def __init__(
        self,
        S: Span = None,
        V: Span = None,
        I: Span = None,
        O: Span = None,
        C: Span = None,
        A: list = [],
    ):
        """
        

        Parameters
        ----------
        S : Span
            Subject.
        V : Span
            Verb.
        I : Span, optional
            Indirect object, The default is None.
        O : Span, optional
            Direct object. The default is None.
        C : Span, optional
            Complement. The default is None.
        A : list, optional
            List of adverbials. The default is [].

        Returns
        -------
        None.

        """
        self.S = S
        self.V = V
        self.I = I
        self.O = O
        self.C = C
        self.A = A

        self.doc = self.S.doc

        complementP = self.C is not None
        adverbialP = len(self.A) > 0
        ext_copular = (
            self.V is not None and self.V.root.lemma_ in dictionary["ext_copular"]
        )
        non_ext_copular = (
            self.V is not None and self.V.root.lemma_ in dictionary["non_ext_copular"]
        )
        conservative = MOD_CONSERVATIVE
        direct_object = self.O is not None
        indirect_object = self.I is not None
        objectP = direct_object or indirect_object
        complex_transitive = (
            self.V is not None
            and self.V.root.lemma_ in dictionary["complex_transitive"]
        )

        self.type = "undefined"

        if self.V is None:
            self.type = "SVC"
            return
        if all([not objectP, complementP]):
            self.type = "SVC"
        if all([not objectP, not complementP, not adverbialP]):
            self.type = "SV"
        if all([not objectP, not complementP, adverbialP, non_ext_copular]):
            self.type = "SV"
        if all(
            [not objectP, not complementP, adverbialP, not non_ext_copular, ext_copular]
        ):
            self.type = "SVA"
        if all(
            [
                not objectP,
                not complementP,
                adverbialP,
                not non_ext_copular,
                not ext_copular,
            ]
        ):
            if conservative:
                self.type = "SVA"
            else:
                self.type = "SV"
        if all([objectP, direct_object, indirect_object]):
            self.type = "SVOO"
        if all([objectP, not (direct_object and indirect_object)]):
            if complementP:
                self.type = "SVOC"
            elif not (adverbialP and direct_object):
                self.type = "SVO"
            elif complex_transitive:
                self.type = "SVOA"
            else:
                if conservative:
                    self.type = "SVOA"
                else:
                    self.type = "SVO"

    def __repr__(self):
        return "<{}, {}, {}, {}, {}, {}, {}>".format(
            self.type, self.S, self.V, self.I, self.O, self.C, self.A
        )

    def to_propositions(self, as_text: bool = False):

        propositions = []

        if self.S:
            subjects = extract_ccs_from_token(self.S.root)
        else:
            subjects = []

        if self.V:
            verbs = [self.V]
        else:
            verbs = []

        if self.I:
            iobjs = extract_ccs_from_token(self.I.root)
        else:
            iobjs = []

        if self.O:
            dobjs = extract_ccs_from_token(self.O.root)
        else:
            dobjs = []

        if self.C:
            comps = extract_ccs_from_token(self.C.root)
        else:
            comps = []

        for subj in subjects:
            if len(verbs) == 0:
                if len(comps) > 0:
                    for c in comps:
                        propositions.append((subj, "is", c))
                    propositions.append((subj, "is") + tuple(comps))
            for verb in verbs:
                prop = [subj, verb]
                if self.type in ["SV", "SVA"]:
                    if len(self.A) > 0:
                        for a in self.A:
                            propositions.append(tuple(prop + [a]))
                        propositions.append(tuple(prop + self.A))
                    else:
                        propositions.append(tuple(prop))

                elif self.type in ["SVOO"]:
                    for iobj in iobjs:
                        for dobj in dobjs:
                            propositions.append((subj, verb, iobj, dobj))
                elif self.type in ["SVO"]:
                    for obj in dobjs + iobjs:
                        propositions.append((subj, verb, obj))
                        if len(self.A) > 0:
                            for a in self.A:
                                propositions.append((subj, verb, obj, a))
                elif self.type in ["SVOA"]:
                    for obj in dobjs:
                        if len(self.A) > 0:
                            for a in self.A:
                                propositions.append(tuple(prop + [obj, a]))
                            propositions.append(tuple(prop + [obj] + self.A))

                elif self.type in ["SVOC"]:
                    for obj in iobjs + dobjs:
                        if len(comps) > 0:
                            for c in comps:
                                propositions.append(tuple(prop + [obj, c]))
                            propositions.append(tuple(prop + [obj] + comps))
                elif self.type in ["SVC"]:
                    if len(comps) > 0:
                        for c in comps:
                            propositions.append(tuple(prop + [c]))
                        propositions.append(tuple(prop + comps))

        # Remove doubles
        if len(propositions) > 0:
            propositions = list(set(propositions))

        if as_text:
            return [" ".join([str(t) for t in p]) for p in propositions]
        return propositions


def extract_clauses(span):
    clauses = []
    # 1. Find verb phrases in the span
    # (see mdmjsh answer here: https://stackoverflow.com/questions/47856247/extract-verb-phrases-using-spacy)

    verb_matcher = Matcher(span.vocab)
    verb_matcher.add(
        "Auxiliary verb phrase aux-verb", None, [{"POS": "AUX"}, {"POS": "VERB"}]
    )
    verb_matcher.add("Auxiliary verb phrase", None, [{"POS": "AUX"}])
    verb_matcher.add("Verb phrase", None, [{"POS": "VERB"}])

    matches = verb_matcher(span)

    # Filter matches (e.g. do not have both "has won" and "won" in verbs)
    verb_chunks = []
    for match in [span[start:end] for _, start, end in matches]:
        if match.root not in [vp.root for vp in verb_chunks]:
            verb_chunks.append(match)

    for verb in verb_chunks:
        # 1.b. find `subject` for verb
        subject = None
        for c in verb.root.children:
            if c.dep_ in ["nsubj", "nsubjpass"]:
                subject = extract_span_from_entity(c)
                break
        if not subject:
            root = verb.root
            while root.dep_ in ["conj", "cc", "advcl"]:
                for c in root.children:
                    if c.dep_ in ["nsubj", "nsubjpass"]:
                        subject = extract_span_from_entity(c)
                        break
                if subject:
                    break
                else:
                    root = verb.root.head

            for c in root.children:
                if c.dep_ in ["nsubj", "nsubj:pass", "nsubjpass"]:
                    subject = extract_span_from_entity(c)
                    break

        if not subject:
            continue

        # Check if there are phrases of the form, "AE, a scientist of ..."
        # If so, add a new clause of the form:
        # <AE, is, a scientist>
        for c in subject.root.children:
            if c.dep_ in ["appos"]:
                comp = extract_span_from_entity(c)
                clause = Clause(subject, None, [], [], comp, [])
                clauses.append(clause)

        # 1.c. find indirect object
        iob = None
        for c in verb.root.children:
            if c.dep_ in ["dative"]:
                iob = extract_span_from_entity(c)

        # 1.d. find direct object
        dob = None
        for c in verb.root.children:
            if c.dep_ in ["dobj"]:
                dob = extract_span_from_entity(c)

        # 1.e. find complements
        comp = None
        for c in verb.root.children:
            if c.dep_ in ["ccomp", "acomp", "xcomp", "attr"]:
                comp = extract_span_from_entity(c)

        # 1.f. find adverbials
        adv = []
        for c in verb.root.children:
            if c.dep_ in ["prep", "advmod", "agent"]:
                adv.append(extract_span_from_entity(c))

        clause = Clause(subject, verb, iob, dob, comp, adv)
        clauses.append(clause)
    return clauses


def extract_clauses_doc(doc):
    for sent in doc.sents:
        clauses = extract_clauses(sent)
        sent._.clauses = clauses
        doc._.clauses += clauses
    return doc


def add_to_pipe(nlp):
    nlp.add_pipe(extract_clauses_doc)


def extract_span_from_entity(token):
    ent_subtree = sorted([c for c in token.subtree], key=lambda x: x.i)
    return Span(token.doc, start=ent_subtree[0].i, end=ent_subtree[-1].i + 1)


def extract_span_from_entity_no_cc(token):
    ent_subtree = sorted(
        [token] + [c for c in token.children if c.dep_ not in ["cc", "conj", "prep"]],
        key=lambda x: x.i,
    )
    return Span(token.doc, start=ent_subtree[0].i, end=ent_subtree[-1].i + 1)


def extract_ccs_from_entity(token):
    entities = [extract_span_from_entity_no_cc(token)]
    for c in token.children:
        if c.dep_ in ["conj", "cc"]:
            entities += extract_ccs_from_entity(c)
    return entities


def extract_ccs_from_token(token):
    if token.pos_ in ["NOUN", "PROPN", "ADJ"]:
        children = sorted(
            [token]
            + [
                c
                for c in token.children
                if c.dep_ in ["advmod", "amod", "det", "poss", "compound"]
            ],
            key=lambda x: x.i,
        )
        entities = [Span(token.doc, start=children[0].i, end=children[-1].i + 1)]
    else:
        entities = [Span(token.doc, start=token.i, end=token.i + 1)]
    for c in token.children:
        if c.dep_ in ["conj"]:
            entities += extract_ccs_from_token(c)
    return entities


if __name__ == "__main__":
    import spacy

    nlp = spacy.load("en")
    add_to_pipe(nlp)

    doc = nlp(
        "Chester is a banker by trade, but is dreaming of becoming a great dancer."
    )

    print(doc._.clauses)
    for clause in doc._.clauses:
        print(clause.to_propositions(as_text=False))
    print(doc[:].noun_chunks)
