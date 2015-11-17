## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "Meresco RDF"
#
# "Meresco RDF" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco RDF" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco RDF"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from collections import defaultdict

from weightless.core import compose

from .uri import Uri
from ._utils import unique
from meresco.xml import namespaces as defaultNamespaces
from ._uris import LABEL_PREDICATES


UNICODE_LABEL_PREDICATES = [unicode(p) for p in LABEL_PREDICATES]

class Graph(object):
    def __init__(self, namespaces=None):
        self._tripleDict = defaultdict(set)
        self.namespaces = namespaces or defaultNamespaces

    def addTriple(self, subject, predicate, object):
        subject, predicate = unicodeOrNone(subject), unicodeOrNone(predicate)
        t = (subject, predicate, object)
        for s in [None, subject]:
            for p in [None, predicate]:
                for o in [None, object]:
                    self._tripleDict[(s, p, o)].add(t)

    def removeTriple(self, subject, predicate, object):
        subject, predicate = unicodeOrNone(subject), unicodeOrNone(predicate)
        t = (subject, predicate, object)
        for s in [None, subject]:
            for p in [None, predicate]:
                for o in [None, object]:
                    tripleSet = self._tripleDict.get((s, p, o))
                    if tripleSet is None:
                        continue
                    tripleSet.discard(t)
                    if not tripleSet:
                        del self._tripleDict[(s, p, o)]

    def triples(self, subject=None, predicate=None, object=None):
        return self._triples(subject=unicodeOrNone(subject), predicate=unicodeOrNone(predicate), object=object)

    def objects(self, subject, predicate=None, curie=None):
        # predicate or predicate-curie (Compact URIs) is required.
        subject, predicate = unicodeOrNone(subject), unicodeOrNone(predicate)
        if predicate is None and not curie is None:
            predicate = self.namespaces.curieToUri(curie)
        return [o for s, p, o in self._triples(subject=subject, predicate=predicate, object=None)]

    def literalValue(self, *args, **kwargs):
        for node in self.objects(*args, **kwargs):
            if node.isLiteral() and node.value:
                return node.value

    def findLabel(self, uri, labelPredicates=UNICODE_LABEL_PREDICATES):
        # uri *as string*
        labels = {}
        for p in labelPredicates:
            for _, _, o in self._triples(subject=unicodeOrNone(uri), predicate=p, object=None):
                language = o.lang
                if language == 'nl':
                    return o
                if language not in labels:
                    labels[language] = o

        label = labels.get('en') or labels.get(None)
        return label

    def __contains__(self, triple):
        return triple in self._tripleDict

    def matchTriplePatterns(self, *triplePatterns):
        def matchRecursive(patterns, bindings):
            if not patterns:
                yield bindings
                return
            pattern, patternsTail = patterns[0], patterns[1:]
            if len(pattern) != 3:
                raise ValueError("%s should have been a triple" % repr(pattern))
            tripleMask = list(pattern)
            variables = {}
            for i, value in enumerate(pattern):
                try:
                    isVariable = value.startswith('?')
                except AttributeError:
                    isVariable = False
                if isVariable:
                    variable = value[1:]
                    variables[i] = variable
                    binding = bindings.get(variable)
                    tripleMask[i] = getattr(binding, 'value', binding) if i < 2 else binding
            for triple in self.triples(*tripleMask):
                newBindings = dict(bindings)
                for i, value in enumerate(triple):
                    variable = variables.get(i)
                    if not variable is None:
                        newBindings[variable] = Uri(value) if i < 2 else value
                yield matchRecursive(patterns=patternsTail, bindings=newBindings)
        return unique(
            compose(matchRecursive(patterns=triplePatterns, bindings={})),
            key=lambda d: tuple(sorted(d.items())))

    def _triples(self, subject, predicate, object):
        return list(self._tripleDict.get((subject, predicate, object), []))


def unicodeOrNone(aString):
    return None if aString is None else unicode(aString)
