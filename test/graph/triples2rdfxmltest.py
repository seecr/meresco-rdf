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

from unittest import skip
from seecr.test import SeecrTestCase, CallTrace

from meresco.components import lxmltostring
from meresco.core import Observable

from meresco.rdf.graph import Graph, Triples2RdfXml, Literal, Uri, BNode
from meresco.xml.namespaces import curieToUri, namespaces
from weightless.core import consume, be


class Triples2RdfXmlTest(SeecrTestCase):
    def testEmptyGraphAsRdfXml(self):
        class A():
            def triples(self):
                return (x for x in [])
        a = A()
        self.assertEquals('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>', lxmltostring(Triples2RdfXml().asRdfXml(a)))

    def testSingleTripleAsRdfXml(self):
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s>
    <rdf:Description rdf:about="http://example.org/item">
        <rdfs:label xml:lang="nl">The Item</rdfs:label>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml().asRdfXml([('http://example.org/item', curieToUri('rdfs:label'), Literal('The Item', lang="nl"))]))

    def testMoreThanOneTriplePerSubjectAsRdfXml(self):
        graph = Graph()
        graph.addTriple('http://example.org/item', curieToUri('rdfs:label'), Literal('The Item', lang="en"))
        graph.addTriple('http://example.org/item', curieToUri('dcterms:creator'), Literal('The Creator'))
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.org/item">
        <dcterms:creator>The Creator</dcterms:creator>
        <rdfs:label xml:lang="en">The Item</rdfs:label>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml().asRdfXml(graph))

    def testRdfResource(self):
        graph = Graph()
        graph.addTriple('http://example.org/item', curieToUri('dcterms:creator'), Uri('http://example.org/theCreator'))
        self.assertXmlEquals('''<rdf:RDF %(xmlns_rdf)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.org/item">
        <dcterms:creator rdf:resource="http://example.org/theCreator"/>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml().asRdfXml(graph))

    def testRdfDescriptionPerUri(self):
        graph = Graph()
        graph.addTriple('http://example.org/item', curieToUri('dcterms:creator'), Uri('http://example.org/theCreator'))
        graph.addTriple('http://example.org/theCreator', curieToUri('rdfs:label'), Literal('The Creator'))
        graph.addTriple('http://example.org/somethingEntirelyDifferent', curieToUri('dcterms:title'), Literal('Something Entirely Different'))
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
</rdf:RDF>''' % namespaces, Triples2RdfXml().asRdfXml(graph))

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
</rdf:RDF>''' % namespaces, Triples2RdfXml().asRdfXml(graph))

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
</rdf:RDF>''' % namespaces, Triples2RdfXml().asRdfXml(graph))

    def testLxmlNodeInsteadOfGraphJustPasses(self):
        observer = CallTrace(emptyGeneratorMethods=['add'])
        t = Triples2RdfXml()
        t.addObserver(observer)

        consume(t.add(identifier='identifier', lxmlNode='lxmlNode'))

        self.assertEquals(['add'], observer.calledMethodNames())
        self.assertEquals(dict(identifier='identifier', lxmlNode='lxmlNode'), observer.calledMethods[0].kwargs)

    def testDeleteJustPasses(self):
        observer = CallTrace(emptyGeneratorMethods=['delete'])
        dna = be((Observable(),
            (Triples2RdfXml(),
                (observer,)
            )
        ))
        consume(dna.all.delete(identifier='whatever'))
        self.assertEquals(['delete'], observer.calledMethodNames())

    def testAnnotation(self):
        graph = Graph()
        body = BNode()
        uri = 'uri:a'
        targetUri = 'uri:target'
        graph.addTriple(subject=uri, predicate=curieToUri('oa:hasBody'), object=body)
        graph.addTriple(subject=uri, predicate=curieToUri('rdf:type'), object=Uri(curieToUri('oa:Annotation')))
        graph.addTriple(subject=uri, predicate=curieToUri('oa:annotatedBy'), object=Uri("uri:testAnnotation"))
        graph.addTriple(subject=uri, predicate=curieToUri('oa:motivatedBy'), object=Uri("uri:testAnnotation:motive"))
        graph.addTriple(subject=uri, predicate=curieToUri('oa:hasTarget'), object=Uri(targetUri))
        graph.addTriple(subject=body, predicate=curieToUri('dcterms:title'), object=Literal("Title"))
        graph.addTriple(subject=body, predicate=curieToUri('dcterms:source'), object=Uri("uri:source"))
        graph.addTriple(subject=Uri("uri:source"), predicate=curieToUri('rdfs:label'), object=Literal("A Source"))

        self.assertXmlEquals('''<rdf:RDF %(xmlns_dcterms)s %(xmlns_oa)s %(xmlns_rdf)s %(xmlns_rdfs)s>
    <oa:Annotation rdf:about="uri:a">
      <oa:annotatedBy rdf:resource="uri:testAnnotation"/>
      <oa:hasBody>
        <rdf:Description>
            <dcterms:source>
                <rdf:Description rdf:about="uri:source">
                    <rdfs:label>A Source</rdfs:label>
                </rdf:Description>
            </dcterms:source>
            <dcterms:title>Title</dcterms:title>
        </rdf:Description>
      </oa:hasBody>
      <oa:hasTarget rdf:resource="uri:target"/>
      <oa:motivatedBy rdf:resource="uri:testAnnotation:motive"/>
    </oa:Annotation>
</rdf:RDF>''' % namespaces, Triples2RdfXml(inlineDescriptions=True).asRdfXml(graph))

        self.assertXmlEquals('''<rdf:RDF %(xmlns_dcterms)s %(xmlns_oa)s %(xmlns_rdf)s %(xmlns_rdfs)s>
    <oa:Annotation rdf:about="uri:a">
      <oa:annotatedBy rdf:resource="uri:testAnnotation"/>
      <oa:hasBody>
        <rdf:Description>
            <dcterms:source rdf:resource="uri:source"/>
            <dcterms:title>Title</dcterms:title>
        </rdf:Description>
      </oa:hasBody>
      <oa:hasTarget rdf:resource="uri:target"/>
      <oa:motivatedBy rdf:resource="uri:testAnnotation:motive"/>
    </oa:Annotation>
    <rdf:Description rdf:about="uri:source">
        <rdfs:label>A Source</rdfs:label>
    </rdf:Description>
</rdf:RDF>''' % namespaces, Triples2RdfXml().asRdfXml(graph))

    @skip('not yet')
    def testIdentifiedBNode(self):
        self.fail()


