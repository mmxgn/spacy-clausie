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
import typing

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
        subject: typing.Optional[Span] = None,
        verb: typing.Optional[Span] = None,
        indirect_object: typing.Optional[Span] = None,
        direct_object: typing.Optional[Span] = None,
        complement: typing.Optional[Span] = None,
        adverbials: typing.List[Span] = None,
    ):
        """


        Parameters
        ----------
        subject : Span
            Subject.
        verb : Span
            Verb.
        indirect_object : Span, optional
            Indirect object, The default is None.
        direct_object : Span, optional
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
            self.type,
            self.subject,
            self.verb,
            self.indirect_object,
            self.direct_object,
            self.complement,
            self.adverbials,
        )

    def to_propositions(
        self, as_text: bool = False, inflect: str or None = "VBD", capitalize: bool = False
    ):

        if inflect and not as_text:
            logging.warning("`inflect' argument is ignored when `as_text==False'. To suppress this warning call `to_propositions' with the argument `inflect=None'")
        if capitalize and not as_text:
            logging.warning("`capitalize' argument is ignored when `as_text==False'. To suppress this warning call `to_propositions' with the argument `capitalize=False")

        propositions = []

        subjects = extract_ccs_from_token_at_root(self.subject)
        direct_objects = extract_ccs_from_token_at_root(self.direct_object)
        indirect_objects = extract_ccs_from_token_at_root(self.indirect_object)
        complements = extract_ccs_from_token_at_root(self.complement)
        verbs = [self.verb] if self.verb else []

        for subj in subjects:
            if complements and not verbs:
                for c in complements:
                    propositions.append((subj, "is", c))
                propositions.append((subj, "is") + tuple(complements))

            for verb in verbs:
                prop = [subj, verb]
                if self.type in ["SV", "SVA"]:
                    if self.adverbials:
                        for a in self.adverbials:
                            propositions.append(tuple(prop + [a]))
                        propositions.append(tuple(prop + self.adverbials))
                    else:
                        propositions.append(tuple(prop))

                elif self.type == "SVOO":
                    for iobj in indirect_objects:
                        for dobj in direct_objects:
                            propositions.append((subj, verb, iobj, dobj))
                elif self.type == "SVO":
                    for obj in direct_objects + indirect_objects:
                        propositions.append((subj, verb, obj))
                        for a in self.adverbials:
                            propositions.append((subj, verb, obj, a))
                elif self.type == "SVOA":
                    for obj in direct_objects:
                        if self.adverbials:
                            for a in self.adverbials:
                                propositions.append(tuple(prop + [obj, a]))
                            propositions.append(tuple(prop + [obj] + self.adverbials))

                elif self.type == "SVOC":
                    for obj in indirect_objects + direct_objects:
                        if complements:
                            for c in complements:
                                propositions.append(tuple(prop + [obj, c]))
                            propositions.append(tuple(prop + [obj] + complements))
                elif self.type == "SVC":
                    if complements:
                        for c in complements:
                            propositions.append(tuple(prop + [c]))
                        propositions.append(tuple(prop + complements))

        # Remove doubles
        propositions = list(set(propositions))

        if as_text:
            return _convert_clauses_to_text(
                propositions, inflect=inflect, capitalize=capitalize
            )

        return propositions


def inflect_token(token, inflect):
    if (
        inflect
        and token.pos_ == "VERB"
        and "AUX" not in [tt.pos_ for tt in token.lefts]
        # t is not preceded by an auxiliary verb (e.g. `the birds were ailing`)
        and token.dep_ != "pcomp"
    ):  # t `dreamed of becoming a dancer`
        return str(token._.inflect(inflect))
    else:
        return str(token)


def _convert_clauses_to_text(propositions, inflect, capitalize):
    proposition_texts = []
    for proposition in propositions:
        span_texts = []
        for span in proposition:

            token_texts = []
            for token in span:
                token_texts.append(inflect_token(token, inflect))

            span_texts.append(" ".join(token_texts))
        proposition_texts.append(" ".join(span_texts))

    if capitalize:  # Capitalize and add a full stop.
        proposition_texts = [text.capitalize() + "." for text in proposition_texts]

    return proposition_texts


def _get_verb_matches(span):
    # 1. Find verb phrases in the span
    # (see mdmjsh answer here: https://stackoverflow.com/questions/47856247/extract-verb-phrases-using-spacy)

    verb_matcher = Matcher(span.vocab)
    verb_matcher.add("Auxiliary verb phrase aux-verb", [
        [{"POS": "AUX"}, {"POS": "VERB"}]])
    verb_matcher.add("Auxiliary verb phrase", [[{"POS": "AUX"}]])
    verb_matcher.add("Verb phrase", [[{"POS": "VERB"}]],)

    return verb_matcher(span)


def _get_verb_chunks(span):
    matches = _get_verb_matches(span)

    # Filter matches (e.g. do not have both "has won" and "won" in verbs)
    verb_chunks = []
    for match in [span[start:end] for _, start, end in matches]:
        if match.root not in [vp.root for vp in verb_chunks]:
            verb_chunks.append(match)
    return verb_chunks


def _get_subject(verb):
    for c in verb.root.children:
        if c.dep_ in ["nsubj", "nsubjpass"]:
            subject = extract_span_from_entity(c)
            return subject

    root = verb.root
    while root.dep_ in ["conj", "cc", "advcl", "acl", "ccomp", "ROOT"]:
        for c in root.children:
            if c.dep_ in ["nsubj", "nsubjpass"]:
                subject = extract_span_from_entity(c)
                return subject

            if c.dep_ in ["acl", "advcl"]:
                subject = find_verb_subject(c)
                return extract_span_from_entity(subject) if subject else None

        # Break cycles
        if root == verb.root.head:
            break
        else:
            root = verb.root.head

    for c in root.children:
        if c.dep_ in ["nsubj", "nsubj:pass", "nsubjpass"]:
            subject = extract_span_from_entity(c)
            return subject
    return None


def _find_matching_child(root, allowed_types):
    for c in root.children:
        if c.dep_ in allowed_types:
            return extract_span_from_entity(c)
    return None


def extract_clauses(span):
    clauses = []

    verb_chunks = _get_verb_chunks(span)
    for verb in verb_chunks:

        subject = _get_subject(verb)
        if not subject:
            continue

        # Check if there are phrases of the form, "AE, a scientist of ..."
        # If so, add a new clause of the form:
        # <AE, is, a scientist>
        for c in subject.root.children:
            if c.dep_ == "appos":
                complement = extract_span_from_entity(c)
                clause = Clause(subject=subject, complement=complement)
                clauses.append(clause)

        indirect_object = _find_matching_child(verb.root, ["dative"])
        direct_object = _find_matching_child(verb.root, ["dobj"])
        complement = _find_matching_child(
            verb.root, ["ccomp", "acomp", "xcomp", "attr"]
        )
        adverbials = [
            extract_span_from_entity(c)
            for c in verb.root.children
            if c.dep_ in ("prep", "advmod", "agent")
        ]

        clause = Clause(
            subject=subject,
            verb=verb,
            indirect_object=indirect_object,
            direct_object=direct_object,
            complement=complement,
            adverbials=adverbials,
        )
        clauses.append(clause)
    return clauses

@spacy.Language.component('claucy')
def extract_clauses_doc(doc):
    for sent in doc.sents:
        clauses = extract_clauses(sent)
        sent._.clauses = clauses
        doc._.clauses += clauses
    return doc


def add_to_pipe(nlp):
    nlp.add_pipe('claucy')


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


def extract_ccs_from_token_at_root(span):
    if span is None:
        return []
    else:
        return extract_ccs_from_token(span.root)


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
        if c.dep_ == "conj":
            entities += extract_ccs_from_token(c)
    return entities


def find_verb_subject(v):
    """
    Returns the nsubj, nsubjpass of the verb. If it does not exist and the root is a head,
    find the subject of that verb instead.
    """
    if v.dep_ in ["nsubj", "nsubjpass", "nsubj:pass"]:
        return v
    # guard against infinite recursion on root token
    elif v.dep_ in ["advcl", "acl"] and v.head.dep_ != "ROOT":
        return find_verb_subject(v.head)

    for c in v.children:
        if c.dep_ in ["nsubj", "nsubjpass", "nsubj:pass"]:
            return c
        elif c.dep_ in ["advcl", "acl"] and v.head.dep_ != "ROOT":
            return find_verb_subject(v.head)


if __name__ == "__main__":
    import spacy

    nlp = spacy.load("en_core_web_sm")
    add_to_pipe(nlp)

    doc = nlp(
        # "Chester is a banker by trade, but is dreaming of becoming a great dancer."
        " A cat , hearing that the birds in a certain aviary were ailing dressed himself up as a physician , and , taking his cane and a bag of instruments becoming his profession , went to call on them ."
    )

    print(doc._.clauses)
    for clause in doc._.clauses:
        print(clause.to_propositions(as_text=True, capitalize=True))
    print(doc[:].noun_chunks)
