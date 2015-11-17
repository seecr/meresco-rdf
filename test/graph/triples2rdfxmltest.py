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

from unittest import skip
from seecr.test import SeecrTestCase

from meresco.components import lxmltostring

from meresco.rdf.graph import Graph, Triples2RdfXml, Literal, Uri, BNode
from meresco.xml.namespaces import curieToUri, namespaces


class Triples2RdfXmlTest(SeecrTestCase):
    def testEmptyGraphAsRdfXml(self):
        class A():
            def triples(self):
                return (x for x in [])
        a = A()
        self.assertEquals('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>', lxmltostring(Triples2RdfXml.asRdfXml(a)))

    def testSingleTripleAsRdfXml(self):
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s>
    <rdf:Description rdf:about="http://example.org/item">
        <rdfs:label xml:lang="nl">The Item</rdfs:label>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml.asRdfXml([('http://example.org/item', curieToUri('rdfs:label'), Literal('The Item', lang="nl"))]))

    def testMoreThanOneTriplePerSubjectAsRdfXml(self):
        class A():
            def triples(self):
                return [
                    ('http://example.org/item', curieToUri('rdfs:label'), Literal('The Item', lang="en")),
                    ('http://example.org/item', curieToUri('dcterms:creator'), Literal('The Creator')),
                ]
        a = A()
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.org/item">
        <dcterms:creator>The Creator</dcterms:creator>
        <rdfs:label xml:lang="en">The Item</rdfs:label>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml.asRdfXml(a))

    def testRdfResource(self):
        class A():
            def triples(self):
                return [
                    ('http://example.org/item', curieToUri('dcterms:creator'), Uri('http://example.org/theCreator')),
                ]
        a = A()
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.org/item">
        <dcterms:creator rdf:resource="http://example.org/theCreator"/>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml.asRdfXml(a))

    def testRdfDescriptionPerUri(self):
        class A():
            def triples(self):
                return [
                    ('http://example.org/item', curieToUri('dcterms:creator'), Uri('http://example.org/theCreator')),
                    ('http://example.org/theCreator', curieToUri('rdfs:label'), Literal('The Creator')),
                    ('http://example.org/somethingEntirelyDifferent', curieToUri('dcterms:title'), Literal('Something Entirely Different'))
                ]
        a = A()
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.org/item">
        <dcterms:creator rdf:resource="http://example.org/theCreator"/>
    </rdf:Description>
    <rdf:Description rdf:about="http://example.org/somethingEntirelyDifferent">
      <dcterms:title>Something Entirely Different</dcterms:title>
    </rdf:Description>
    <rdf:Description rdf:about="http://example.org/theCreator">
      <rdfs:label>The Creator</rdfs:label>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml.asRdfXml(a))

    def testAnonymousBNode(self):
        graph = Graph()
        graph.addTriple('http://example.org/item', curieToUri('dcterms:creator'), BNode('_:1'))
        graph.addTriple('_:1', curieToUri('rdfs:label'), Literal('The Creator', lang='en'))
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.org/item">
        <dcterms:creator>
            <rdf:Description>
                <rdfs:label xml:lang="en">The Creator</rdfs:label>
            </rdf:Description>
        </dcterms:creator>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml.asRdfXml(graph))

    def testNestedAnonymousBNode(self):
        graph = Graph()
        for triple in [
            ('http://example.org/item', curieToUri('dcterms:creator'), BNode('_:1')),
            ('_:1', curieToUri('rdfs:label'), Literal('The Creator', lang='en')),
            ('_:1', curieToUri('dcterms:spatial'), BNode('_:2')),
            ('_:2', curieToUri('geo:lat'), Literal('123.123')),
            ('_:2', curieToUri('geo:long'), Literal('1.3')),
        ]:
            graph.addTriple(*triple)
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_dcterms)s %(xmlns_geo)s>
    <rdf:Description rdf:about="http://example.org/item">
        <dcterms:creator>
            <rdf:Description>
                <dcterms:spatial>
                    <rdf:Description>
                        <geo:lat>123.123</geo:lat>
                        <geo:long>1.3</geo:long>
                    </rdf:Description>
                </dcterms:spatial>
                <rdfs:label xml:lang="en">The Creator</rdfs:label>
            </rdf:Description>
        </dcterms:creator>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml.asRdfXml(graph))

    @skip('not yet')
    def testIdentifiedBNode(self):
        self.fail()


