# ClauCy
Implementation of the ClausIE information extraction system for python+spacy. 

**Disclaimer**: This is **not** meant to be a 1-1 implementation of the algorithm 
(which is impossible since SpaCy is used instead of Stanford Dependencies like in the paper) 
but a clause extraction and text simplification library I have for personal use. 

I have made some modifications. 
- I did some exploration on how to better separate embedded clauses when using SpaCy dependencies. 
- I provide the ability to *inflect* the verbs, so that they are in a somewhat useful text form 
when generating propositions in text. 

This allows the processing of complex sentences such as this:
```
A cat, hearing that the birds in a certain aviary were ailing dressed himself up as a physician, 
and, taking his cane and a bag of instruments becoming his profession, went to call on them.
```

to produce propositions such as these:

```
['The birds were ailing.']
['A cat dressed himself as a physician.', 'A cat dressed himself.']
['A cat took his cane.', 'A cat took a bag.']
['A cat became his profession.']
['A cat went.']
['A cat called on them.']
```

## Changelog from v 0.1.0

- Rewrote it to match more closely the algorithm in the paper.
- Reimplemented it as a `spacy` pipeline component (clauses under `doc._.clauses`)
- Added tests from the paper

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
- `spacy>=3.0.0`
- `lemminflect>=0.2.1` (only if using the `inflect` argument in `to_propositions(as_text=True)`)
- Python 3

## Installation
```
$ git clone https://github.com/mmxgn/spacy-clausie.git
$ cd spacy-clausie
$ python setup.py build 
$ python setup.py install [--user]

# Optionally
$ python setup.py test
```

Or with pip:

```sh
python -m pip install git+https://github.com/mmxgn/spacy-clausie.git
```

Download the pipeline if necessary:

```sh
python -m spacy download en_core_web_sm
```

## Usage

### Python

```
$ ipython
In [1]: import spacy                                                                                                                                               
In [2]: import claucy                                                                                                                                               
In [3]: nlp = spacy.load("en_core_web_sm")
In [4]: claucy.add_to_pipe(nlp)                                                                                                                                     
In [5]: doc = nlp("AE died in Princeton in 1955.")                                                                                                                 
In [6]: doc._.clauses                                                                                                                                               
Out[6]: [<SV, AE, died, None, None, None, [in Princeton, in 1955]>]
In [7]: propositions = doc._.clauses[0].to_propositions(as_text=True)                                                                                               
In [8]: propositions                                                                                                                                               
Out[8]: 
['AE died in Princeton in 1955',
 'AE died in 1955',
 'AE died in Princeton']
```

Setting `as_text=False` will instead give a tuple of spacy spans:

```
In [9]: propositions = doc._.clauses[0].to_propositions(as_text=False)                                                                                             
In [10]: propositions                                                                                                                                               
Out[10]: 
[(AE, died, in Princeton, in 1955),
 (AE, died, in 1955),
 (AE, died, in Princeton)]
```

### Problog

Copy `problog/claucy_pl.py` at the same directory as your problog `.pl` files, include it 
in your scripts with:

```
:- use_module('claucy_pl.py').
```

And use it via the `claucy/4` predicate. An example can be seen in `problog/test_clausie.pl`:

```
:-use_module('claucy_pl.py').

query(claucy('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',Predicate,Arg1,Arg2)).
```

You can run it with:

```
problog test_claucy.pl
```

and get the output:

```
     claucy('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',died,Albert Einstein,in 1955):       1         
claucy('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',died,Albert Einstein,in Princeton):       1         
   claucy('Albert Einstein, a scientist of the 20th century, died in Princeton in 1955.',is,Albert Einstein,a scientist):       1      
```

The variable `Predicate` comes directly from the verb and `Arg1` and `Arg2` are the first and second arguments.



## License

This code is licensed under the [General Public License Version 3.0](https://www.gnu.org/licenses/gpl-3.0.txt). 
