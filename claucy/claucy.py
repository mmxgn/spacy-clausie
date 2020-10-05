#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  6 18:07:24 2019

@author: Emmanouil Theofanis Chourdakis

Clausie as a spacy library
"""

import spacy
import lemminflect
import logging
import typing as t

from spacy.tokens import Span, Doc
from spacy.matcher import Matcher
from lemminflect import getInflection

logging.basicConfig(level=logging.INFO)

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
            subject: t.Optional[Span] = None,
            verb: t.Optional[Span] = None,
            indirect_object: t.Optional[Span] = None,
            direct_object: t.Optional[Span] = None,
            complement: t.Optional[Span] = None,
            adverbials: t.List[Span] = None,
    ):
        """
        

        Parameters
        ----------
        subject : Span
            Subject.
        verb : Span
            Verb.
        has_indirect_object : Span, optional
            Indirect object, The default is None.
        has_direct_object : Span, optional
            Direct object. The default is None.
        complement : Span, optional
            Complement. The default is None.
        adverbials : list, optional
            List of adverbials. The default is [].

        Returns
        -------
        None.

        """
        if adverbials is None:
            adverbials = []

        self.subject = subject
        self.verb = verb
        self.indirect_object = indirect_object
        self.direct_object = direct_object
        self.complement = complement
        self.adverbials = adverbials

        self.doc = self.subject.doc

        self.type = self._get_clause_type()

    def _get_clause_type(self):
        has_verb = self.verb is not None
        has_complement = self.complement is not None
        has_adverbial = len(self.adverbials) > 0
        has_ext_copular_verb = (
                has_verb and self.verb.root.lemma_ in dictionary["ext_copular"]
        )
        has_non_ext_copular_verb = (
                has_verb and self.verb.root.lemma_ in dictionary["non_ext_copular"]
        )
        conservative = MOD_CONSERVATIVE
        has_direct_object = self.direct_object is not None
        has_indirect_object = self.indirect_object is not None
        has_object = has_direct_object or has_indirect_object
        complex_transitive = (
                has_verb and self.verb.root.lemma_ in dictionary["complex_transitive"]
        )

        clause_type = "undefined"
        # # Original
        # if not has_verb:
        #     clause_type = "SVC"
        #     return clause_type
        # if all([not has_object, has_complement]):
        #     clause_type = "SVC"
        #
        # if all([not has_object, not has_complement, not has_adverbial]):
        #     clause_type = "SV"
        # if all([not has_object, not has_complement, has_adverbial, has_non_ext_copular_verb]):
        #     clause_type = "SV"
        #
        # if all(
        #         [not has_object, not has_complement, has_adverbial, not has_non_ext_copular_verb, has_ext_copular_verb]
        # ):
        #     clause_type = "SVA"
        # if all(
        #     [
        #         not has_object,
        #         not has_complement,
        #         has_adverbial,
        #         not has_non_ext_copular_verb,
        #         not has_ext_copular_verb,
        #     ]
        # ):
        #     if conservative:
        #         clause_type = "SVA"
        #     else:
        #         clause_type = "SV"
        #
        # if all([has_object, has_direct_object, has_indirect_object]):
        #     clause_type = "SVOO"
        # if all([has_object, not (has_direct_object and has_indirect_object)]):
        #     if has_complement:
        #         clause_type = "SVOC"
        #     elif not (has_adverbial and has_direct_object):
        #         clause_type = "SVO"
        #     elif complex_transitive:
        #         clause_type = "SVOA"
        #     else:
        #         if conservative:
        #             clause_type = "SVOA"
        #         else:
        #             clause_type = "SVO"

        if not has_verb:
            clause_type = "SVC"
            return clause_type

        if has_object:
            if has_direct_object and has_indirect_object:
                clause_type = "SVOO"
            elif has_complement:
                clause_type = "SVOC"
            elif not has_adverbial or not has_direct_object:
                clause_type = "SVO"
            elif complex_transitive or conservative:
                clause_type = "SVOA"
            else:
                clause_type = "SVO"
        else:
            if has_complement:
                clause_type = "SVC"
            elif not has_adverbial or has_non_ext_copular_verb:
                clause_type = "SV"
            elif has_ext_copular_verb or conservative:
                clause_type = "SVA"
            else:
                clause_type = "SV"

        return clause_type

    def __repr__(self):
        return "<{}, {}, {}, {}, {}, {}, {}>".format(
            self.type, self.subject, self.verb, self.indirect_object, self.direct_object, self.complement,
            self.adverbials
        )

    def to_propositions(self, as_text: bool = False, inflect: str = "VBD", capitalize: bool = False):

        if inflect and not as_text:
            logging.warning("`inflect' argument is ignored when `as_text==False'")
        if capitalize and not as_text:
            logging.warning("`capitalize' agrument is ignored when `as_text==False'")

        propositions = []

        subjects = extract_ccs_from_token(self.subject.root)
        iobjs = extract_ccs_from_token(self.indirect_object.root)
        dobjs = extract_ccs_from_token(self.direct_object.root)
        comps = extract_ccs_from_token(self.complement.root)
        verbs = [self.verb] if self.verb else []


        for subj in subjects:
            if len(verbs) == 0:
                if len(comps) > 0:
                    for c in comps:
                        propositions.append((subj, "is", c))
                    propositions.append((subj, "is") + tuple(comps))
            for verb in verbs:
                prop = [subj, verb]
                if self.type in ["SV", "SVA"]:
                    if len(self.adverbials) > 0:
                        for a in self.adverbials:
                            propositions.append(tuple(prop + [a]))
                        propositions.append(tuple(prop + self.adverbials))
                    else:
                        propositions.append(tuple(prop))

                elif self.type in ["SVOO"]:
                    for iobj in iobjs:
                        for dobj in dobjs:
                            propositions.append((subj, verb, iobj, dobj))
                elif self.type in ["SVO"]:
                    for obj in dobjs + iobjs:
                        propositions.append((subj, verb, obj))
                        if len(self.adverbials) > 0:
                            for a in self.adverbials:
                                propositions.append((subj, verb, obj, a))
                elif self.type in ["SVOA"]:
                    for obj in dobjs:
                        if len(self.adverbials) > 0:
                            for a in self.adverbials:
                                propositions.append(tuple(prop + [obj, a]))
                            propositions.append(tuple(prop + [obj] + self.adverbials))

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

        # Convert to text if `as_text' is set.
        if as_text:
            texts = [
                " ".join(
                    [
                        " ".join(
                            [
                                str(
                                    t._.inflect(inflect)
                                )  # Inflect the verb according to the `inflect` flag
                                if t.pos_ in ["VERB"]  # If t is a verb
                                   and "AUX"
                                   not in [
                                       tt.pos_ for tt in t.lefts
                                   ]  # t is not preceded by an auxiliary verb (e.g. `the birds were ailing`)
                                   and t.dep_ not in ['pcomp']  # t `deamed of becoming a dancer`
                                   and inflect  # and the `inflect' flag is set
                                else str(t)
                                for t in s
                            ]
                        )
                        for s in p
                    ]
                )
                for p in propositions
            ]

            if capitalize:
                # Capitalize and add a full stop.
                return [text.capitalize() + "." for text in texts]
            else:
                return texts

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
            while root.dep_ in ["conj", "cc", "advcl", "acl", "ccomp"]:
                for c in root.children:
                    if c.dep_ in ["nsubj", "nsubjpass"]:
                        subject = extract_span_from_entity(c)
                        break
                    if c.dep_ in ["acl", "advcl"]:
                        subject = extract_span_from_entity(find_verb_subject(c))
                if subject:
                    break
                else:
                    # Break cycles
                    if root == verb.root.head:
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
    if token is None:
        return []
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


def find_verb_subject(v):
    """
    Returns the nsubj, nsubjpass of the verb. If it does not exist and the root is a head,
    find the subject of that verb instead. 
    """
    if v.dep_ in ["nsubj", "nsubjpass", "nsubj:pass"]:
        return v
    elif v.dep_ in ["advcl", "acl"]:
        return find_verb_subject(v.head)

    for c in v.children:
        if c.dep_ in ["nsubj", "nsubjpass", "nsubj:pass"]:
            return c
        elif c.dep_ in ["advcl", "acl"]:
            return find_verb_subject(v.head)


if __name__ == "__main__":
    import spacy

    nlp = spacy.load("en")
    add_to_pipe(nlp)

    doc = nlp(
        # "Chester is a banker by trade, but is dreaming of becoming a great dancer."
        " A cat , hearing that the birds in a certain aviary were ailing dressed himself up as a physician , and , taking his cane and a bag of instruments becoming his profession , went to call on them ."
    )

    print(doc._.clauses)
    for clause in doc._.clauses:
        print(clause.to_propositions(as_text=True, capitalize=True))
    print(doc[:].noun_chunks)
