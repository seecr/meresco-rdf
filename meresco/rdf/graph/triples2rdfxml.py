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

from functools import partial
from collections import defaultdict

from lxml.etree import cleanup_namespaces

from meresco.core import Transparent
from meresco.xml.utils import createElement as _createElement, createSubElement as _createSubElement

from meresco.xml.namespaces import namespaces as defaultNamespaces
from .graph import Graph


class Triples2RdfXml(Transparent):
    """Transparent to allow for passing on delete message"""
    def add(self, graph, **kwargs):
        yield self.all.add(lxmlNode=self.asRdfXml(graph), **kwargs)

    @classmethod
    def asRdfXml(cls, triplesOrGraph, namespaces=None):
        graph = triplesOrGraph
        if not hasattr(triplesOrGraph, 'triples'):
            graph = Graph()
            for s, p, o in triplesOrGraph:
                graph.addTriple(s, p, o)
        triples2RdfXml = Triples2RdfXml_(graph=graph, namespaces=namespaces)
        return triples2RdfXml.asRdfXml()


class Triples2RdfXml_(object):
    def __init__(self, graph, namespaces=None):
        self.graph = graph
        self.namespaces = namespaces or defaultNamespaces
        self.createElement = partial(_createElement, namespaces=self.namespaces)
        self.createSubElement = partial(_createSubElement, namespaces=self.namespaces)

    def asRdfXml(self):
        rdfElement = self.createElement('rdf:RDF', nsmap=self.namespaces)
        uriDescriptions = defaultdict(list)
        for (s, p, o) in self.graph.triples():
            if not s.startswith('_:'):
                uriDescriptions[s].append((p, o))
        for s, relations in sorted(uriDescriptions.iteritems()):
            description = self.createSubElement(rdfElement, 'rdf:Description', attrib={'rdf:about': s})
            self.serializeDescription(description, relations)
        cleanup_namespaces(rdfElement)
        return rdfElement

    def serializeDescription(self, descriptionNode, relations):
        for (p, o) in sorted(relations):
            text = None
            attrib = {}
            if o.isLiteral():
                if o.lang:
                    attrib = {'xml:lang': o.lang}
                text = o.value
            elif o.isUri():
                attrib={'rdf:resource': o.value}

            predicate = self.createSubElement(descriptionNode, self.namespaces.uriToCurie(p), attrib=attrib, text=text)

            if o.isBNode():
                bnodeRelations = []
                for (s, p, o) in self.graph.triples(subject=o.value):
                    bnodeRelations.append((p, o))
                bnodeDescription = self.createSubElement(predicate, 'rdf:Description')
                self.serializeDescription(bnodeDescription, bnodeRelations)
