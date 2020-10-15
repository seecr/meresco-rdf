## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2014-2016, 2018, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from functools import partial
from collections import defaultdict

from lxml.etree import cleanup_namespaces

from meresco.core import Transparent
from meresco.xml.utils import createElement as _createElement, createSubElement as _createSubElement
from meresco.xml.namespaces import namespaces as defaultNamespaces, curieToUri, curieToTag

from .graph import Graph
from .uri import Uri
from .bnode import BNode


class Triples2RdfXml(Transparent):
    def __init__(self, namespaces=None, inlineDescriptions=False, knownTypes=None, relativeTypePositions=None, **kwargs):
        Transparent.__init__(self, **kwargs)
        namespaces=namespaces or defaultNamespaces
        self._Triples2RdfXml = partial(_Triples2RdfXml,
            namespaces=namespaces,
            createElement=partial(_createElement, namespaces=namespaces),
            createSubElement=partial(_createSubElement, namespaces=namespaces),
            inlineDescriptions=inlineDescriptions,
            nodePromotedTypes=dict((namespaces.curieToUri(t), t) for t in (NODE_PROMOTED_TYPES.union(knownTypes or []))),
            relativeTypePositions=dict(RELATIVE_TYPE_POSITIONS, **(relativeTypePositions or {}))
        )

    def add(self, **kwargs):
        if 'graph' in kwargs:
            kwargs['lxmlNode'] = self.asRdfXml(kwargs.pop('graph'))
        yield self.all.add(**kwargs)

    def asRdfXml(self, triplesOrGraph):
        graph = triplesOrGraph
        if not hasattr(triplesOrGraph, 'matchTriplePatterns'):
            graph = Graph()
            triples = triplesOrGraph
            if hasattr(triples, 'triples'):
                triples = triples.triples()
            for s, p, o in triples:
                graph.addTriple(s, p, o)
        triples2RdfXml = self._Triples2RdfXml(graph=graph)
        return triples2RdfXml.asRdfXml()


class _Triples2RdfXml(object):
    def __init__(self, graph, **kwargs):
        self.graph = graph
        self.__dict__.update(kwargs)
        self._relationRdfIds = self._gatherRelationRdfIds()

    def asRdfXml(self):
        rdfElement = self.createElement('rdf:RDF', nsmap=self.namespaces)
        resourceDescriptions = defaultdict(lambda: {'types': set(), 'relations': []})
        for (s, p, o) in self.graph.triples():
            if s.startswith('_:'):
                if len(self._leftHandSides(BNode(s))) == 1:
                    continue
            self._gatherRelation(resourceDescriptions[s], p, o)

        sortedSubjects = [s for s, _ in sorted(list(resourceDescriptions.items()), key=self._subjectUriOrder)]
        for subject in sortedSubjects:
            try:
                resourceDescription = resourceDescriptions.pop(subject)
            except KeyError:
                continue
            tagCurie = self._tagCurieForNode(subject, resourceDescription)
            attrib = None
            if not subject.startswith('_:'):
                attrib = {'rdf:about': subject}
            else:
                if len(self._leftHandSides(BNode(subject))) > 0:
                    attrib = {'rdf:nodeID': subject.partition('_:')[-1]}
            descriptionNode = self.createSubElement(rdfElement, tagCurie, attrib=attrib)
            self.serializeDescription(descriptionNode, subject, resourceDescription, resourceDescriptions)
        cleanup_namespaces(rdfElement)
        return rdfElement

    def _gatherRelationRdfIds(self):
        relationRdfIds = {}
        for binding in self.graph.matchTriplePatterns(
                ('?r', RDF_SUBJECT, '?s'),
                ('?r', RDF_PREDICATE, '?p'),
                ('?r', RDF_OBJECT, '?o')):
            r, key = binding['r'].value, (binding['s'].value, binding['p'].value, binding['o'])
            if not r.startswith('_:'):
                relationRdfIds[key] = r.partition("#")[-1]
        return relationRdfIds

    def serializeDescription(self, descriptionNode, subject, resourceDescription, uriDescriptions):
        for (p, o) in sorted(resourceDescription['relations']):
            if descriptionNode.tag == RDF_STATEMENT_TAG:
                if descriptionNode.attrib.get(RDF_ABOUT_TAG) and p in REIFICATION_RELATIONS:
                    continue
            text = None
            attrib = {}
            oResourceDescription = {'relations': [], 'types': set()}
            rdfID = self._relationRdfIds.get((subject, p, o), None)
            if rdfID:
                attrib['rdf:ID'] = rdfID
            if o.isIdentifier():
                for (_, p1, o1) in self.graph.triples(subject=o.value):
                    self._gatherRelation(oResourceDescription, p1, o1)
                if o.isUri() and (not self.inlineDescriptions or not oResourceDescription['relations']):
                    attrib['rdf:resource'] = o.value
                elif o.isBNode() and len(self._leftHandSides(o)) > 1:
                    attrib['rdf:nodeID'] = o.value.partition('_:')[-1]
            elif o.isLiteral():
                if o.lang:
                    attrib['xml:lang'] = o.lang
                text = o.value
            predicateNode = self.createSubElement(descriptionNode, self.namespaces.uriToCurie(p), attrib=attrib, text=text)
            if 'rdf:nodeID' in attrib or not oResourceDescription['relations']:
                continue
            if o.isBNode() or self.inlineDescriptions:
                attrib = {}
                if o.isUri():
                    attrib['rdf:about'] = o.value
                tag = self._tagCurieForNode(o, oResourceDescription)
                nodeElement = self.createSubElement(predicateNode, tag, attrib=attrib)
                uriDescriptions.pop(o.value, None)
                self.serializeDescription(nodeElement, o.value, oResourceDescription, uriDescriptions)

    def _leftHandSides(self, o):
        return set(s for s, lhsP, _ in self.graph.triples(object=o) if lhsP != RDF_SUBJECT)

    def _gatherRelation(self, resourceDescription, p, o):
        resourceDescription['relations'].append((p, o))
        if p == RDF_TYPE:
            resourceDescription['types'].add(o.value)

    def _tagCurieForNode(self, uri, resourceDescription):
        rdfTypes = resourceDescription['types']
        for rdfType in rdfTypes:
            typeTagCurie = self.nodePromotedTypes.get(rdfType)
            if typeTagCurie:
                resourceDescription['relations'].remove((RDF_TYPE, Uri(rdfType)))
                return typeTagCurie
        return 'rdf:Description'

    def _subjectUriOrder(self, xxx_todo_changeme):
        (s, resourceDescription) = xxx_todo_changeme
        return (
            min([self.relativeTypePositions.get(type, 0) for type in resourceDescription['types']] or [0]),
            len(self._leftHandSides(BNode(s) if s.startswith('_:') else Uri(s))),
            -len(resourceDescription['relations']),
            s
        )


RDF_STATEMENT_TAG = curieToTag('rdf:Statement')
RDF_ABOUT_TAG = curieToTag('rdf:about')

RDF_TYPE = curieToUri('rdf:type')
RDF_SUBJECT = curieToUri('rdf:subject')
RDF_PREDICATE = curieToUri('rdf:predicate')
RDF_OBJECT = curieToUri('rdf:object')
REIFICATION_RELATIONS = set([RDF_SUBJECT, RDF_PREDICATE, RDF_OBJECT])

NODE_PROMOTED_TYPES = set(['rdf:Statement', 'oa:Annotation'])

RELATIVE_TYPE_POSITIONS = {
    curieToUri('oa:Annotation'): -10,
    curieToUri('rdf:Statement'): 100,
}
