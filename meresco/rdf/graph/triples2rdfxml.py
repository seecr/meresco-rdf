## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2014-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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
from meresco.xml.namespaces import namespaces as defaultNamespaces, curieToUri
from .graph import Graph


class Triples2RdfXml(Transparent):
    def __init__(self, namespaces=None, inlineDescriptions=False, knownTypes=None, **kwargs):
        Transparent.__init__(self, **kwargs)
        namespaces=namespaces or defaultNamespaces
        self._Triples2RdfXml = partial(_Triples2RdfXml,
            namespaces=namespaces,
            createElement=partial(_createElement, namespaces=namespaces),
            createSubElement=partial(_createSubElement, namespaces=namespaces),
            inlineDescriptions=inlineDescriptions,
            knownTypes=dict((namespaces.curieToUri(t), t) for t in (knownTypes or ['oa:Annotation'])),
        )

    def add(self, **kwargs):
        if 'graph' in kwargs:
            kwargs['lxmlNode'] = self.asRdfXml(kwargs.pop('graph'))
        yield self.all.add(**kwargs)

    def asRdfXml(self, triplesOrGraph):
        graph = triplesOrGraph
        if not hasattr(triplesOrGraph, 'triples'):
            graph = Graph()
            for s, p, o in triplesOrGraph:
                graph.addTriple(s, p, o)
        triples2RdfXml = self._Triples2RdfXml(graph=graph)
        return triples2RdfXml.asRdfXml()


class _Triples2RdfXml(object):
    def __init__(self, graph, **kwargs):
        self.graph = graph
        for k,v in kwargs.items():
            setattr(self, k, v)

    def asRdfXml(self):
        rdfElement = self.createElement('rdf:RDF', nsmap=self.namespaces)
        uriDescriptions = defaultdict(list)
        for (s, p, o) in self.graph.triples():
            if not s.startswith('_:'):
                uriDescriptions[s].append((p, o))
        while uriDescriptions:
            sWithMostRelations = [s for s, _ in sorted(uriDescriptions.items(), key=lambda (s, relations):-len(relations))][0]
            relations = uriDescriptions.pop(sWithMostRelations)
            tag = self._tagForRelations(sWithMostRelations, relations)
            description = self.createSubElement(rdfElement, tag, attrib={'rdf:about': sWithMostRelations})
            self.serializeDescription(description, relations, uriDescriptions)
        cleanup_namespaces(rdfElement)
        return rdfElement

    def serializeDescription(self, descriptionNode, relations, uriDescriptions):
        for (p, o) in sorted(relations):
            text = None
            attrib = {}
            relations = []
            if o.isUri() or o.isBNode():
                for (_, p1, o1) in self.graph.triples(subject=o.value):
                    relations.append((p1, o1))
            if o.isLiteral():
                if o.lang:
                    attrib = {'xml:lang': o.lang}
                text = o.value
            elif o.isUri() and (not self.inlineDescriptions or not relations):
                attrib={'rdf:resource': o.value}

            predicate = self.createSubElement(descriptionNode, self.namespaces.uriToCurie(p), attrib=attrib, text=text)

            if not relations:
                continue

            if o.isBNode() or self.inlineDescriptions:
                attrib = {}
                if o.isUri():
                    attrib={'rdf:about': o.value}
                    uriDescriptions.pop(o.value, None)

                tag = self._tagForRelations(o, relations)
                bnodeDescription = self.createSubElement(predicate, tag, attrib=attrib)
                self.serializeDescription(bnodeDescription, relations, uriDescriptions)

    def _tagForRelations(self, uri, relations):
        rdfTypes = self.graph.objects(subject=uri, predicate=RDF_TYPE)
        if rdfTypes:
            rdfType = rdfTypes[0]
            typeTag = self.knownTypes.get(rdfType.value)
            if typeTag:
                relations.remove((RDF_TYPE, rdfType))
                return typeTag
        return 'rdf:Description'

RDF_TYPE = curieToUri('rdf:type')
