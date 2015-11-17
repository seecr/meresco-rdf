## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2013-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
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

from seecr.test import SeecrTestCase
from seecr.test.io import stdout_replaced

from os import makedirs
from os.path import join, dirname, abspath
from shutil import copy

from lxml.etree import parse
from StringIO import StringIO

from meresco.xml.namespaces import namespaces, curieToUri
from meresco.rdf.graph import Literal, Uri, BNode, GraphComponent

mydir = dirname(abspath(__file__))
rdfDir = join(dirname(mydir), 'data')

class GraphComponentTest(SeecrTestCase):
    def testMakeGraph(self):
        with stdout_replaced():
            g = GraphComponent(rdfSources=[])
        g = g.makeGraph(parseXml(RDF_XML))
        self.assertEquals(set([
                ('uri:uri', namespaces.dcterms + 'title', Literal('The title')),
                ('uri:uri', namespaces.rdf + 'type', Uri('type:type#'))
            ]),
            set(list(g.triples(None, None, None)))
        )

    def testTriples(self):
        with stdout_replaced():
            g = GraphComponent(rdfSources=[])
        g = g.makeGraph(parseXml(RDF_XML))
        self.assertEquals([('uri:uri', namespaces.dcterms + 'title', Literal('The title'))], list(g.triples(subject='uri:uri', predicate=namespaces.dcterms + 'title')))
        self.assertEquals([('uri:uri', namespaces.dcterms + 'title', Literal('The title'))], list(g.triples(subject=None, predicate=namespaces.dcterms + 'title', object=Literal('The title'))))
        self.assertEquals([('uri:uri', namespaces.rdf + 'type', Uri('type:type#'))], list(g.triples(object=Uri('type:type#'))))
        self.assertEquals(1, len(list(g.triples(object=Uri('type:type#')))))
        self.assertEquals(1, len(list(g.triples(subject='uri:uri', predicate=namespaces.rdf+'type', object=Uri('type:type#')))))

    def testFindLabelUsingRealOntology(self):
        subdir = join(self.tempdir, 'subdir')
        makedirs(subdir)
        copy(join(rdfDir, 'nl_property_labels.rdf'), subdir)
        with stdout_replaced():
            g = GraphComponent(rdfSources=[self.tempdir])
        self.assertEquals(Literal('Titel', lang='nl'), g.findLabel(namespaces.dcterms + 'title'))
        self.assertEquals(Literal('Maker', lang='nl'), g.findLabel(namespaces.dcterms + 'creator'))
        self.assertEquals(Literal('Tijd', lang='nl'), g.findLabel("http://purl.org/NET/c4dm/event.owl#time"))

    def testTriplesUsingRealOntology(self):
        subdir = join(self.tempdir, 'subdir')
        makedirs(subdir)
        copy(join(rdfDir, 'nl_property_labels.rdf'), subdir)
        with stdout_replaced():
            g = GraphComponent(rdfSources=[self.tempdir])

        self.assertTrue(10 < len(list(g.triples())), list(g.triples()))
        self.assertEquals([
                (namespaces.curieToUri('dcterms:title'),
                 namespaces.curieToUri('rdfs:label'),
                 Literal('Titel', lang='nl')
                )
            ],
            list(g.triples(
                subject=namespaces.curieToUri('dcterms:title'),
                predicate=namespaces.curieToUri('rdfs:label'))),
        )

    def testGraphNavigationByTriples(self):
        with stdout_replaced():
            gc = GraphComponent(rdfSources=[])
        g = gc.makeGraph(lxmlNode=parseXml(RDF_XML_NAVIGATION))

        result = list(g.triples(subject='uri:nav', predicate=namespaces.dcterms+'publisher'))
        self.assertEquals(1, len(result))
        self.assertEquals(
            ('uri:nav', namespaces.dcterms+'publisher'),
            result[0][:2])
        bnode = result[0][2]
        self.assertTrue(isinstance(bnode, BNode))

        result = list(g.triples(subject=bnode.value))
        self.assertEquals(
            [(bnode.value, namespaces.rdfs+'label', Literal('Pub'))],
            result)

    def testInitializeGraphComponentFromRdfObjects(self):
        class A(object):
            @property
            def context(self):
                return 'uri:context'

            def asRdfXml(self):
                yield '''\
<rdf:RDF
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <rdf:Description rdf:about="uri:someUri">
        <rdfs:label xml:lang="nl">Some resource</rdfs:label>
    </rdf:Description>
</rdf:RDF>'''

        with stdout_replaced():
            gc = GraphComponent(rdfSources=[A()])
        self.assertEquals([("uri:someUri", curieToUri("rdfs:label"), Literal("Some resource", lang="nl"))], list(gc.triples()))

def parseXml(data):
    return parse(StringIO(data))


RDF_XML = '''<rdf:RDF %(xmlns_rdf)s>
<rdf:Description %(xmlns_dcterms)s rdf:about="uri:uri">
    <rdf:type rdf:resource="type:type#" />
    <dcterms:title>The title</dcterms:title>
</rdf:Description>
</rdf:RDF>''' % namespaces

RDF_XML_NAVIGATION = '''<rdf:RDF %(xmlns_rdf)s>
<rdf:Description %(xmlns_dcterms)s %(xmlns_rdfs)s rdf:about="uri:nav">
    <dcterms:publisher>
        <rdf:Description>
            <rdfs:label>Pub</rdfs:label>
        </rdf:Description>
    </dcterms:publisher>
</rdf:Description>
</rdf:RDF>''' % namespaces

