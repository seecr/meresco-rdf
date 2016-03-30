# -*- coding: utf-8 -*-
## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  initiated by Stichting Bibliotheek.nl to provide a new search service
#  for all public libraries in the Netherlands.
#
# Copyright (C) 2014 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
#
# This file is part of "NBC+ (Zoekplatform BNL)"
#
# "NBC+ (Zoekplatform BNL)" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NBC+ (Zoekplatform BNL)" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NBC+ (Zoekplatform BNL)"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase

from meresco.xml.namespaces import namespaces, curieToUri

from os.path import join, dirname, abspath

from lxml.etree import XML, parse

from meresco.rdf.graph.rdfparser import RDFParser, getText
from meresco.rdf.graph import Uri, Literal, BNode, Graph


mydir = dirname(abspath(__file__))
testDatadir = join(dirname(mydir), 'data')

class RdfParserTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.sink = Graph()

    def testOne(self):
        RDFParser(sink=self.sink).parse(XML(INPUT_RDF))
        objects = sorted(list(self.sink.objects(subject=uri, curie="rdfs:seeAlso")))
        self.assertEquals(sorted([Uri('http://example.com'), Literal('http://example.org')]), objects)

    def testConvenienceGraph(self):
        graph = RDFParser().parse(XML(INPUT_RDF))
        objects = sorted(list(graph.objects(subject=uri, curie="rdfs:seeAlso")))
        self.assertEquals(sorted([Uri('http://example.com'), Literal('http://example.org')]), objects)

    def testTypeFromElementTag(self):
        based_xml = '''<rdf:RDF
        %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_owl)s
        xml:base="http://purl.org/ontology/mo/"
        >
        <owl:Class rdf:about="Track">
            <rdfs:label>track</rdfs:label>
            <rdfs:subClassOf rdf:resource="MusicalManifestation"/>
        </owl:Class>
        </rdf:RDF>''' % namespaces
        RDFParser(sink=self.sink).parse(XML(based_xml))
        self.assertEquals([Uri(namespaces.owl + 'Class')], list(self.sink.objects(subject='http://purl.org/ontology/mo/Track', curie='rdf:type')))

    def testParseNodeWithoutRdfContainer(self):
        xml = '''<owl:Class %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_owl)s rdf:about="http://purl.org/ontology/mo/Track">
            <rdfs:label>track</rdfs:label>
            <rdfs:subClassOf rdf:resource="http://purl.org/ontology/mo/MusicalManifestation"/>
        </owl:Class>''' % namespaces
        RDFParser(sink=self.sink).parse(XML(xml))
        self.assertEquals([Uri(namespaces.owl + 'Class')], list(self.sink.objects(subject='http://purl.org/ontology/mo/Track', curie='rdf:type')))

    def testLiteralWithCommentAndPI(self):
        RDFParser(sink=self.sink).parse(XML(INPUT_RDF))
        self.assertEquals(sorted([Literal('1970'), Literal('1970-01-01')], key=lambda l: (l.value, l.lang)), sorted([o for s,p,o in self.sink.triples(subject=uri, predicate=namespaces.curieToUri('dcterms:date'))], key=lambda l: (l.value, l.lang)))

    def testBlankNodesAndLiterals(self):
        BNode.nextGenId = 0
        RDFParser(sink=self.sink).parse(XML(INPUT_RDF))
        self.assertEquals([BNode('_:id0')], list(self.sink.objects(subject=uri, curie='dcterms:creator')))
        self.assertEquals([Uri("http://dbpedia.org/ontology/Person")], list(self.sink.objects(subject='_:id0', curie='rdf:type')))

        contributor = self.sink.objects(subject=uri, predicate=namespaces.curieToUri('dcterms:contributor'))[0]
        self.assertEquals([Literal('Anonymous', lang="en")], list(self.sink.objects(subject=contributor.value, curie='rdfs:label')))

        self.assertTrue(Literal('An illustrated history of Black Americans', lang="en") in set(self.sink.objects(subject=uri, curie='dcterms:title')))

    def testBase(self):
        RDFParser(sink=self.sink).parse(XML(RDF_WITH_BASE))
        self.assertEquals([
                ('http://example.org/base/2', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', Uri('http://example.org/base/Book')),
            ], list(self.sink.triples()))

    def testBase2(self):
        based_xml = '''<rdf:RDF
        %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_owl)s
        xml:base="http://purl.org/ontology/mo/"
        >
        <owl:Class rdf:about="Track">
            <rdfs:label>track</rdfs:label>
            <rdfs:subClassOf rdf:resource="MusicalManifestation"/>
        </owl:Class>
        </rdf:RDF>''' % namespaces
        RDFParser(sink=self.sink).parse(XML(based_xml))
        self.assertTrue(('http://purl.org/ontology/mo/Track', 'http://www.w3.org/2000/01/rdf-schema#subClassOf', Uri('http://purl.org/ontology/mo/MusicalManifestation')) in set(self.sink.triples()))

    def testParsingEntitiesNoProblem(self):
        custom_type_relations_rdf = parse(open(join(testDatadir, 'custom_type_relations.rdf')))
        RDFParser(sink=self.sink).parse(custom_type_relations_rdf)

        self.assertTrue(('http://purl.org/ontology/mo/Track', 'http://www.w3.org/2000/01/rdf-schema#subClassOf', Uri('http://dbpedia.org/ontology/MusicalWork')) in set(self.sink.triples()))

    def testEmptyPropertyAttribs(self):
        RDFParser(sink=self.sink).parse(XML(INPUT_RDF))
        relationBnode = self.sink.objects(subject=uri, curie='dcterms:relation')[0]
        self.assertEquals([Literal('JPM')], list(self.sink.objects(subject=relationBnode.value, predicate=namespaces.curieToUri("dcterms:title"))))
        self.assertEquals([Uri(namespaces.curieToUri('foaf:Person'))], list(self.sink.objects(subject=relationBnode.value, curie="rdf:type")))

    def testGetText(self):
        node = XML('<node>v<!-- com -->w<!-- ment -->x<?pro ce?>y<?ss ing?>z</node>')
        self.assertEquals('vwxyz', getText(node))

        node = XML('<node>x<sub>subtext<subsub />subsubtail</sub>y<a><b>text</b>text</a>z</node>')
        self.assertEquals('xyz', getText(node))

        node = XML('<node><a><b /></a></node>')
        self.assertEquals(None, getText(node))

        node = XML('<node> <a><b /></a></node>')
        self.assertEquals(' ', getText(node))

        node = XML('<node><a><b /></a> </node>')
        self.assertEquals(' ', getText(node))

        node = XML('<node><a /> <b /></node>')
        self.assertEquals(' ', getText(node))

        node = XML('<node><!-- comment --></node>')
        self.assertEquals(None, getText(node))

        node = XML('<node><?pi 3.14?></node>')
        self.assertEquals(None, getText(node))

    def testRdfID(self):
        RDFParser(sink=self.sink).parse(XML("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
               xmlns:exterms="http://www.example.com/terms/"
               xml:base="http://www.example.com/2002/04/products">
    <rdf:Description rdf:ID="item10245">
        <exterms:model>Overnighter</exterms:model>
    </rdf:Description>
</rdf:RDF>
"""))
        self.assertEquals([("http://www.example.com/2002/04/products#item10245", "http://www.example.com/terms/model", Literal("Overnighter"))], list(self.sink.triples()))

    def testNodeID(self):
        RDFParser(sink=self.sink).parse(XML("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" %(xmlns_rdfs)s
               xmlns:exterms="http://www.example.com/terms/">
    <rdf:Description rdf:about="http://example.com/something">
        <exterms:relatedTo rdf:nodeID="abc"/>
    </rdf:Description>
    <rdf:Description rdf:nodeID="abc">
        <rdfs:label>ABC</rdfs:label>
    </rdf:Description>
</rdf:RDF>""" % namespaces))
        self.assertEquals([
                ("http://example.com/something", "http://www.example.com/terms/relatedTo", BNode("_:abc")),
                ("_:abc", namespaces.rdfs + 'label', Literal("ABC"))
            ], list(self.sink.triples()))

    def testShouldIgnorePropertyEltWithoutValue(self):
        RDFParser(sink=self.sink).parse(XML("""<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s
               xmlns:exterms="http://www.example.com/terms/">
    <rdf:Description rdf:about="http://example.com/something">
        <exterms:relatedTo/>
    </rdf:Description>
</rdf:RDF>""" % namespaces))
        self.assertEquals([('http://example.com/something', 'http://www.example.com/terms/relatedTo', Literal(''))], list(self.sink.triples()))

    def testShouldRecognizeParseTypeResource(self):
        BNode.nextGenId = 0
        RDFParser(sink=self.sink).parse(XML("""<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.com/something">
        <dcterms:hasFormat rdf:parseType="Resource">
            <dcterms:title>Title</dcterms:title>
            <dcterms:format>application/epub</dcterms:format>
        </dcterms:hasFormat>
    </rdf:Description>
</rdf:RDF>""" % namespaces))
        self.assertEquals(set([
            ("http://example.com/something", curieToUri('dcterms:hasFormat'), BNode('_:id0')),
            ('_:id0', curieToUri('dcterms:format'), Literal('application/epub')),
            ('_:id0', curieToUri('dcterms:title'), Literal('Title')),
        ]), set(self.sink.triples()))

    def testRecognizedRdfIDForReification(self):
        BNode.nextGenId = 0
        RDFParser(sink=self.sink).parse(XML("""<rdf:RDF %(xmlns_rdf)s %(xmlns_rdfs)s %(xmlns_dcterms)s>
    <rdf:Description rdf:about="http://example.com/something">
        <dcterms:title rdf:ID="triple2">Title</dcterms:title>
    </rdf:Description>
    <rdf:Statement rdf:about="#triple2">
        <dcterms:source>source</dcterms:source>
    </rdf:Statement>
</rdf:RDF>""" % namespaces))
        self.assertEquals(set([
            ("http://example.com/something", curieToUri('dcterms:title'), Literal("Title")),
            (u'#triple2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate', Uri(u'http://purl.org/dc/terms/title')),
            (u'#triple2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#object', Literal(u'Title')),
            (u'#triple2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#type', Uri(u'http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement')),
            (u'#triple2', u'http://purl.org/dc/terms/source', Literal(u'source')),
            (u'#triple2', u'http://www.w3.org/1999/02/22-rdf-syntax-ns#subject', Uri(u'http://example.com/something'))
        ]), set(self.sink.triples()))


uri = "urn:GGC:oclc-ggc:780950577"

INPUT_RDF = """
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="urn:GGC:oclc-ggc:780950577">
    </rdf:Description><rdf:Description %(xmlns_rdfs)s %(xmlns_dcterms)s %(xmlns_bibo)s %(xmlns_geo)s %(xmlns_schema)s rdf:about="urn:GGC:oclc-ggc:780950577">
        <rdf:type rdf:resource="http://dbpedia.org/ontology/Book"/>
        <rdf:type rdf:resource="http://dbpedia.org/ontology/FakeBook"/>
        <dcterms:type>Geschiedenis</dcterms:type>
        <rdfs:seeAlso rdf:resource="http://example.com"/>
        <rdfs:seeAlso>http://example.org</rdfs:seeAlso>
        <dcterms:title>An illustrated history of Black Americans </dcterms:title>  <!-- trailing non-breaking space! -->
        <dcterms:title xml:lang="en">An illustrated history of Black Americans</dcterms:title>
        <dcterms:title></dcterms:title>
        <rdfs:label/>
        <dcterms:identifier rdf:resource="urn:GGC:oclc-ggc:780950577"/>
        <dcterms:alternative>Geïllustreerde geschiedenis van zwarte Amerikanen </dcterms:alternative>
        <dcterms:alternative/>
        <dcterms:creator>
            <rdf:Description rdf:type="http://dbpedia.org/ontology/Person">
                <rdfs:label>Franklin, John Hope </rdfs:label>
                <dcterms:isFormatOf rdf:resource="http://data.bibliotheek.nl/ggc/ppn/987654321"/>
            </rdf:Description>
        </dcterms:creator>
        <dcterms:contributor>
            <rdf:Description rdfs:label="Anonymous" xml:lang="en"/>
        </dcterms:contributor>
        <dcterms:date><!--year only-->1970</dcterms:date>
        <dcterms:date><!--
        year -->1970-<!--
        month -->01-<!--
        day -->01</dcterms:date>
        <dcterms:extent>192 p</dcterms:extent>
        <dcterms:publisher>New York : Time-Life Books</dcterms:publisher>
        <dcterms:language rdf:resource="urn:iso:std:iso:639:-2:ger"/>
        <dcterms:description>Geïllustreerde geschiedenis van zwarte Amerikanen</dcterms:description>
        <bibo:isbn rdf:resource="urn:ISBN:999"/>
        <dcterms:issued>1970-01-01</dcterms:issued>
        <dcterms:isFormatOf rdf:resource="http://data.bibliotheek.nl/ggc/ppn/123456789123456789"/>
        <dcterms:isPartOf rdf:resource="http://data.bibliotheek.nl/ggc/ppn/987654321"/>
        <schema:genre>history</schema:genre>
        <geo:lat>50.0</geo:lat>
        <geo:long>6.0</geo:long>
        <dcterms:relation dcterms:title="JPM" rdf:type="http://xmlns.com/foaf/0.1/Person" />
    </rdf:Description>
</rdf:RDF>""" % namespaces

RDF_WITH_BASE = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xml:base="http://example.org/base/">
    <rdf:Description rdf:about="2">
        <rdf:type rdf:resource="Book"/>
    </rdf:Description>
</rdf:RDF>
"""
