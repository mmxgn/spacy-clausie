# clausiepy
Implementation of the ClausIE information extraction system for python+spacy

## Credits
While this is a re-implementation by me, original research work (and also the dictionaries) is attributed to Luciano Del Corro
and Rainer Gemulla. If you use it in your code please note that there are slight modifications in the code in order to make it work with the spacy dependency parser, and also cite:
```
Del Corro Luciano, and Rainer Gemulla: "Clausie: clause-based open information extraction." 
Proceedings of the 22nd international conference on World Wide Web. ACM, 2013.
```

It would be helpful to also cite this specific implementation if you are using it:
```
@InProceedings{chourdakis2018grammar,
author = {Chourdakis, E.T and Reiss, J.D.},
title = {Grammar Informed Sound Effect Retrieval for Soundscape Generation},
booktitle = {DMRN+ 13: Digital Music Research Network One-day Workshop},
month = {November},
year = {2018},
address = {London, UK},
pages={9}
}
```

## Requirements
`spacy>=2.0.0`

## Installation
```
$ git clone https://github.com/mmxgn/clausiepy.git
$ cd clausiepy
$ python3 setup.py build 
$ python3 setup.py install [--user]
```

## Usage

### Python

```
$ ipython3

In [1]: import clausiepy as clausie
In [2]: clauses = clausie.clausie('Albert Einstein died in Princeton in 1955.')
In [3]: clauses
Out[3]: 
[{'S': [Einstein],
  'V': [died],
  'O': [],
  'IO': [],
  'XCOMP': [],
  'C': [],
  'type': 'SV',
  'A?': [in, in]}]
In [4]: propositions = clausie.extract_propositions(clauses)
In [5]: clausie.print_propositions(propositions)
Out [5]:
([Einstein], [died], [], [], [], [])
([Einstein], [died], [], [], [], [in, Princeton])
([Einstein], [died], [], [], [], [in, 1955])
```
Note that `clausie`, and `extract_propositions` here return dictionaries and lists of `spacy` span objects which you
can subsequently use however you like.

### Problog

Copy `problog/clausiepy_pl.py` at the same directory as your problog `.pl` files, include it 
in your scripts with:

```
:- use_module('clausiepy_pl.py').
```

And use it via the `clausie/7` predicate. An example can be seen in `problog/test_clausie.pl`:

```
:-use_module('clausiepy_pl.py').

query(clausie('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.', Subject, Verb, IndirectObject, DirectObject, Complement, Adverb)).

```

You can run it with:

```
problog test_clausie.pl
```

and get the output:

```
                             clausie('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',Einstein,died,,,,):	1         
                      clausie('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',Einstein,died,,,,in 1955):	1         
                 clausie('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',Einstein,died,,,,in Princeton):	1         
clausie('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',Einstein,is,,,a scientist of the 20th century,):	1  
```

The variables `Subject`, `Verb`, etc. are self explanatory.


## License

This code is licensed under the [Creative Commons Attribution-ShareAlike 3.0 Unported License](https://creativecommons.org/licenses/by-sa/3.0/).
