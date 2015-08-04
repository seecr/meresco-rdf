# -*- coding: utf-8 -*-
## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2012-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
# Copyright (C) 2015 Stichting Kennisnet http://www.kennisnet.nl
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

from os.path import join
from StringIO import StringIO
from lxml.etree import parse, cleanup_namespaces, XML

from seecr.test import SeecrTestCase
from seecr.test.io import stdout_replaced, stderr_replaced

from weightless.core import be, consume
from meresco.core import Observable
from meresco.oai import OaiJazz
from meresco.components import lxmltostring
from meresco.sequentialstore import MultiSequentialStorage

from meresco.rdf.plein import Plein
from meresco.xml.namespaces import xpathFirst, xpath
from meresco.xml.utils import createSubElement


class PleinTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.storage = MultiSequentialStorage(join(self.tempdir, 'store'), name='storage')
        self.oaiJazz = OaiJazz(join(self.tempdir, 'oai'), name='oaiJazz')

        self.plein = self._newPlein()
        self.dna = be(
            (Observable(),
                (self.plein,
                    (self.storage,),
                    (self.oaiJazz,),
                )
            ))


    def testAddInitialRecord(self):
        uri = "some:uri"

        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://www.openarchives.org/OAI/2.0/">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
    <prov:wasDerivedFrom xmlns:prov="http://www.w3.org/ns/prov#">
        <prov:Entity>
            <dcterms:source rdf:resource="http://first.example.org"/>
        </prov:Entity>
    </prov:wasDerivedFrom>
</rdf:Description>""" % uri

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription))

        consume(self.dna.all.add(identifier="identifier", lxmlNode=lxmlNode))

        record = self.oaiJazz.getRecord(identifier=uri)
        expected = XML(lxmltostring(xpathFirst(lxmlNode, '//rdf:RDF')))
        cleanup_namespaces(expected)
        self.assertXmlEquals(expected, self.storage.getData(identifier=record.identifier, name='rdf'))

        self.assertEquals(set(['rdf']), record.prefixes)
        self.assertEquals(set(), record.sets)

        self.plein.close()
        plein2 = self._newPlein()
        self.assertEquals(['some:uri'], [fragment.uri for fragment in plein2._fragmentsForRecord('identifier')])

    def testAddWithIgnoredOtherKwarg(self):
        uri = "some:uri"
        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://www.openarchives.org/OAI/2.0/">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
    <prov:wasDerivedFrom xmlns:prov="http://www.w3.org/ns/prov#">
        <prov:Entity>
            <dcterms:source rdf:resource="http://first.example.org"/>
        </prov:Entity>
    </prov:wasDerivedFrom>
</rdf:Description>""" % uri
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription))
        consume(self.dna.all.add(identifier="identifier", lxmlNode=lxmlNode, otherKwarg='ignored'))
        record = self.oaiJazz.getRecord(identifier=uri)
        self.assertTrue(record, record)

    def testAddDescriptionsFor2DifferentUris(self):
        originalIdentifier='original:two_descriptions'
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dcterms="http://purl.org/dc/terms/">
    <skos:Concept rdf:about="http://example.com/first/uri" xmlns:skos="http://www.w3.org/2004/02/skos/core#">
         <skos:prefLabel xml:lang="nl">Eerste</skos:prefLabel>
    </skos:Concept>
    <rdf:Description rdf:about="http://example.com/first/uri">
        <prov:wasDerivedFrom xmlns:prov="http://www.w3.org/ns/prov#">
            <prov:Entity>
                <dcterms:source rdf:resource="http://first.example.org"/>
            </prov:Entity>
        </prov:wasDerivedFrom>
    </rdf:Description>
    <skos:Concept xmlns:skos="http://www.w3.org/2004/02/skos/core#" rdf:about="http://example.com/second/uri">
         <skos:prefLabel xml:lang="nl">Tweede</skos:prefLabel>
    </skos:Concept>
    <skos:Concept xmlns:skos="http://www.w3.org/2004/02/skos/core#" rdf:about="http://example.com/second/uri">
         <skos:prefLabel xml:lang="nl">Tweede</skos:prefLabel>
    </skos:Concept>
    <rdf:Description rdf:about="http://example.com/second/uri">
        <prov:wasDerivedFrom xmlns:prov="http://www.w3.org/ns/prov#">
            <prov:Entity>
                <dcterms:source>Second Source</dcterms:source>
            </prov:Entity>
        </prov:wasDerivedFrom>
    </rdf:Description>
</rdf:RDF>"""))
        consume(self.dna.all.add(identifier=originalIdentifier, partname="ignored", lxmlNode=lxmlNode))

        record1 = self.oaiJazz.getRecord('http://example.com/first/uri')
        data = self.storage.getData(identifier=record1.identifier, name='rdf')
        self.assertTrue('<dcterms:source rdf:resource="http://first.example.org"/>' in data, data)
        self.assertTrue('<skos:prefLabel xml:lang="nl">Eerste</skos:prefLabel>' in data, data)

        record2 = self.oaiJazz.getRecord('http://example.com/second/uri')
        data = self.storage.getData(identifier=record2.identifier, name='rdf')
        self.assertEquals(1, data.count('<skos:prefLabel xml:lang="nl">Tweede</skos:prefLabel>'), data)
        self.assertTrue('<dcterms:source>Second Source</dcterms:source>' in data, data)

    def testAddDescriptionsWithMultipleSameUris(self):
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dcterms="http://purl.org/dc/terms/">
    <skos:Concept rdf:about="http://example.com/first/uri" xmlns:skos="http://www.w3.org/2004/02/skos/core#">
         <skos:prefLabel xml:lang="nl">Eerste</skos:prefLabel>
    </skos:Concept>
</rdf:RDF>"""))
        consume(self.dna.all.add(identifier='original:one_description', partname="ignored", lxmlNode=lxmlNode))

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dcterms="http://purl.org/dc/terms/">
    <skos:Concept rdf:about="http://example.com/first/uri" xmlns:skos="http://www.w3.org/2004/02/skos/core#">
         <skos:prefLabel xml:lang="nl">Tweede</skos:prefLabel>
    </skos:Concept>
</rdf:RDF>"""))
        consume(self.dna.all.add(identifier='original:two_description', partname="ignored", lxmlNode=lxmlNode))

        record = self.oaiJazz.getRecord("http://example.com/first/uri")
        data = self.storage.getData(identifier=record.identifier, name='rdf')
        self.assertTrue('<skos:prefLabel xml:lang="nl">Eerste</skos:prefLabel>' in data, data)
        self.assertTrue('<skos:prefLabel xml:lang="nl">Tweede</skos:prefLabel>' in data, data)

    def testUpdateRecordWithDifferentFragments(self):
        uri = "uri:someuri"
        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
</rdf:Description>""" % uri

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription))
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=lxmlNode))

        record = self.oaiJazz.getRecord(uri)
        data = self.storage.getData(identifier=record.identifier, name='rdf')
        self.assertTrue('<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>' in data, data)

        # now add with new title
        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">new title</dc:title>
</rdf:Description>""" % uri

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription))
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=lxmlNode))

        record = self.oaiJazz.getRecord(uri)
        data = self.storage.getData(identifier=record.identifier, name='rdf')
        self.assertFalse('<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>' in data, data)
        self.assertTrue('<dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">new title</dc:title>' in data, data)

    def testUpdateRecordShouldNotRemoveFragmentThatsInUseByOtherRecord(self):
        uri1 = "uri:someuri 1"
        uri2 = "uri:someuri 2"

        rdfDescription1 = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
</rdf:Description>""" % uri1
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription1))
        consume(self.dna.all.add(identifier="identifier1", partname="ignored", lxmlNode=lxmlNode))
        record1 = self.oaiJazz.getRecord(uri1)

        rdfDescription2 = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="nl">titel</dc:title>
</rdf:Description>""" % uri2
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
        %s
</rdf:RDF>""" % (rdfDescription1, rdfDescription2)))
        consume(self.dna.all.add(identifier="identifier2", partname="ignored", lxmlNode=lxmlNode))
        record2 = self.oaiJazz.getRecord(uri2)

        self.assertEquals(['uri:someuri 1'], [fragment.uri for fragment in self.plein._fragmentsForRecord('identifier1')])
        self.assertEquals(['uri:someuri 1', 'uri:someuri 2'], [fragment.uri for fragment in self.plein._fragmentsForRecord('identifier2')])

        record = self.oaiJazz.getRecord(uri1)
        self.assertEquals(record1.stamp, record.stamp)

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription2))
        consume(self.dna.all.add(identifier="identifier2", partname="ignored", lxmlNode=lxmlNode))

        # nothing has changed from the OAI perspective
        record = self.oaiJazz.getRecord(uri1)
        self.assertFalse(record.isDeleted)
        self.assertEquals(record1.stamp, record.stamp)
        record = self.oaiJazz.getRecord(uri2)
        self.assertEquals(record2.stamp, record.stamp)

        self.plein.close()
        plein2 = self._newPlein()

        self.assertEquals(['uri:someuri 1'], [fragment.uri for fragment in plein2._fragmentsForRecord('identifier1')])
        self.assertEquals(['uri:someuri 2'], [fragment.uri for fragment in plein2._fragmentsForRecord('identifier2')])

    def testRecordUpdateThatOrphansFragmentCausesUriOaiUpdate(self):
        uri1 = "uri:someuri1"
        uri2 = "uri:someuri2"

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
    </rdf:Description>
</rdf:RDF>""" % uri1))
        consume(self.dna.all.add(identifier="identifier1", partname="ignored", lxmlNode=lxmlNode))

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="nl">titel</dc:title>
    </rdf:Description>
</rdf:RDF>""" % uri1))
        consume(self.dna.all.add(identifier="identifier2", partname="ignored", lxmlNode=lxmlNode))

        record1 = self.oaiJazz.getRecord(uri1)

        # now update record 'identifier1' with fragment for different uri
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">another title</dc:title>
    </rdf:Description>
</rdf:RDF>""" % uri2))
        consume(self.dna.all.add(identifier="identifier1", partname="ignored", lxmlNode=lxmlNode))

        record = self.oaiJazz.getRecord(uri1)
        self.assertNotEquals(record1.stamp, record.stamp)

        self.assertEquals(['uri:someuri2'], [fragment.uri for fragment in self.plein._fragmentsForRecord('identifier1')])
        self.assertEquals(['uri:someuri1'], [fragment.uri for fragment in self.plein._fragmentsForRecord('identifier2')])

    def testUpdateRecordThatOrphansUriCausesUriDelete(self):
        uri1 = "uri:someuri1"
        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
</rdf:Description>""" % uri1

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription))
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=lxmlNode))
        record1 = self.oaiJazz.getRecord(uri1)
        self.assertFalse(record1.isDeleted)

        # now add with different uri
        uri2 = "uri:someuri2"
        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">new title</dc:title>
</rdf:Description>""" % uri2

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription))
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=lxmlNode))

        record1 = self.oaiJazz.getRecord(uri1)
        self.assertTrue(record1.isDeleted)

    def testSpecialCharacterInUri(self):
        uri = "some:Baháma's:|have pipes ( | ) and spaces "
        rdfDescription1 = """<rdf:Description xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" rdf:about="%s">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="nl">titel</dc:title>
</rdf:Description>""" % uri

        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription1))
        consume(self.dna.all.add(identifier=unicode(uri), partname="ignored", lxmlNode=lxmlNode))

        record = self.oaiJazz.getRecord(identifier=unicode(uri))
        data = self.storage.getData(identifier=record.identifier, name='rdf')
        self.assertTrue(uri in data, data)

        consume(self.dna.all.delete(identifier=unicode(uri)))
        record = self.oaiJazz.getRecord(identifier=unicode(uri))
        self.assertTrue(record.isDeleted)

    def testDeleteUnseenRecord(self):
        try:
            consume(self.dna.all.delete(identifier="identifier"))
        except:
            # The above delete should just be silently ignored and not raise an exception
            # (as it did on some point).
            self.fail()

    def testDeleteRecordWithUniqueFragment(self):
        uri = "uri:someuri"
        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
</rdf:Description>""" % uri
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">%s</rdf:RDF>""" % rdfDescription))
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=lxmlNode))

        consume(self.dna.all.delete(identifier="identifier"))
        record = self.oaiJazz.getRecord(uri)
        self.assertTrue(record.isDeleted)

    def testDeleteRecordWithNotSoUniqueFragment(self):
        uri1 = "uri:someuri1"
        uri2 = "uri:someuri2"
        rdfDescription1 = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
</rdf:Description>""" % uri1
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription1))
        consume(self.dna.all.add(identifier="identifier1", partname="ignored", lxmlNode=lxmlNode))

        rdfDescription2 = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="nl">titel</dc:title>
</rdf:Description>""" % uri2
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
        %s
</rdf:RDF>""" % (rdfDescription1, rdfDescription2)))
        consume(self.dna.all.add(identifier="identifier2", partname="ignored", lxmlNode=lxmlNode))

        consume(self.dna.all.delete(identifier="identifier2"))
        record = self.oaiJazz.getRecord(uri1)
        self.assertFalse(record.isDeleted)
        record = self.oaiJazz.getRecord(uri2)
        self.assertTrue(record.isDeleted)

    def testAddTwoRecordsWithSameUriAndDeleteLast(self):
        uri = "uri:someuri"
        rdfNode, description = createRdfNode(uri)
        createSubElement(description, "dc:title", text='One')
        consume(self.dna.all.add(identifier="identifier1", partname="ignored", lxmlNode=rdfNode.getroot()))
        rdfNode, description = createRdfNode(uri)
        createSubElement(description, "dc:title", text='Two')
        consume(self.dna.all.add(identifier="identifier2", partname="ignored", lxmlNode=rdfNode.getroot()))
        consume(self.dna.all.delete(identifier="identifier2"))
        record = self.oaiJazz.getRecord(identifier=uri)
        self.assertEquals(['One'], xpath(XML(self.storage.getData(identifier=record.identifier, name='rdf')), '/rdf:RDF/rdf:Description/dc:title/text()'))

    def testAddDeleteAddForSameUri(self):
        uri1 = "uri:someuri1"
        rdfDescription = """<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">title</dc:title>
</rdf:Description>""" % uri1
        lxmlNode = parse(StringIO("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        %s
</rdf:RDF>""" % rdfDescription))
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=lxmlNode))
        record1 = self.oaiJazz.getRecord(uri1)
        self.assertFalse(record1.isDeleted)

        consume(self.dna.all.delete(identifier="identifier"))
        record1 = self.oaiJazz.getRecord(uri1)
        self.assertTrue(record1.isDeleted)

        # a previous bug caused the following to raise an Exception
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=lxmlNode))
        record1 = self.oaiJazz.getRecord(uri1)
        self.assertFalse(record1.isDeleted)

    def testPossibleShutdownAtWrongTime(self):
        # We suspect a bad shutdown could have cause a difference between keyvaluestore and the data.
        uri1 = "uri:someuri1"
        rdfFillTitle = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about="%s" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/" xml:lang="en">%%s</dc:title>
</rdf:Description></rdf:RDF>""" % uri1
        consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=parse(StringIO(rdfFillTitle % 'title'))))
        record1 = self.storage.getData(identifier=uri1, name='rdf')
        self.assertEquals('title', xpathFirst(XML(record1), '/rdf:RDF/rdf:Description/dc:title/text()'))
        # HACK the data in storage, which could have happened if shutdown while adding.
        self.storage.addData(identifier=uri1, name='rdf', data=rdfFillTitle % 'other title')
        # Service is shutdown after adding the uri to the storage, but just before registring the fragmentHashes in the key value store
        # The next call caused a KeyError while removing old fragmentHashes.
        with stderr_replaced():
            consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=parse(StringIO(rdfFillTitle % 'other title'))))

        record1 = self.storage.getData(identifier=uri1, name='rdf')
        self.assertEquals('other title', xpathFirst(XML(record1), '/rdf:RDF/rdf:Description/dc:title/text()'))

    def testSetSpec(self):
        rdfNode, description = createRdfNode('uri:some')
        consume(self.dna.all.add(identifier='identifier', partname='ignored', lxmlNode=rdfNode, oaiArgs={'sets': [('first:example', 'set first:example')]}))
        self.assertEquals(set(['first', 'first:example']), self.oaiJazz.getAllSets())

    def testBackwardsCompatiblePlein(self):
        uri = "http://data.bibliotheek.nl/CDR/JK115700"
        rdfNode, description = createRdfNode(uri)
        self.plein._fragmentAdmin['identifier'] = 'ae5ac42b162064df2cd4ef411b42325b51f91206|%s' % uri
        with stdout_replaced():
            consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=rdfNode))

    def testBackwardsCompatiblePleinSpaces(self):
        uri = "http://data.bibliotheek.nl/CDR/J K11 5700"
        rdfNode, description = createRdfNode(uri)
        self.plein._fragmentAdmin['identifier'] = 'ae5ac42b162064df2cd4ef411b42325b51f91206|%s' % uri
        with stdout_replaced():
            consume(self.dna.all.add(identifier="identifier", partname="ignored", lxmlNode=rdfNode))

    def testFixEncodedFragments(self):
        from meresco.rdf.plein import fixEncodedFragments, _Fragment
        ahash = 'ae5ac42b162064df2cd4ef411b42325b51f91206'
        uri1 = "http://data.bibliotheek.nl/CDR/J K11 5700"
        uri2 = "http://data.bibliotheek.nl/CDR/J K11 5701"
        data = '{0}|{1} {2}'.format(ahash, uri1, _Fragment(uri=uri2, hash=ahash).asEncodedString())
        result = fixEncodedFragments(data)
        self.assertFalse('|' in result)
        fragments = [_Fragment.fromEncodedString(s) for s in result.split(' ')]
        self.assertEquals([uri1, uri2], [f.uri for f in fragments])

    def testFixEncodedFragmentsWithPipes(self):
        from meresco.rdf.plein import fixEncodedFragments, _Fragment
        uri = "http://data.bibliotheek.nl/gids/film/Cultureel_festijn_'de_Franse_maand'_Ernest_en_Celestine_(Brammert_en_Tissie)_|_film_6+"
        ahash = 'ae5ac42b162064df2cd4ef411b42325b51f91206'
        data = '{0}|{1}'.format(ahash, uri)
        result = fixEncodedFragments(data)
        self.assertFalse('|' in result)
        fragments = [_Fragment.fromEncodedString(s) for s in result.split(' ')]
        self.assertEquals([uri], [f.uri for f in fragments])

    def testFixEncodedFragmentsWithSpacesAndPipes(self):
        from meresco.rdf.plein import fixEncodedFragments, _Fragment
        uri = "http://data.bibliotheek.nl/gids/film/Cultureel festijn 'de Franse maand' Ernest en Celestine (Brammert en Tissie) | film 6+"
        ahash = 'ae5ac42b162064df2cd4ef411b42325b51f91206'
        data = '{0}|{1}'.format(ahash, uri)
        result = fixEncodedFragments(data)
        self.assertFalse('|' in result)
        fragments = [_Fragment.fromEncodedString(s) for s in result.split(' ')]
        self.assertEquals([uri], [f.uri for f in fragments])

    def testFixEncodedFragmentsAllOfTheAbove(self):
        from meresco.rdf.plein import fixEncodedFragments, _Fragment
        ahash = 'ae5ac42b162064df2cd4ef411b42325b51f91206'
        uri1 = "http://data.bibliotheek.nl/CDR/J K11 5701"
        uri2 = "http://data.bibliotheek.nl/CDR/J K11 5702"
        uri3 = "http://data.bibliotheek.nl/CDR/J K| 11 57|03"
        uri4 = "http://data.bibliotheek.nl/CDR/J K11 5704"
        data = '{ahash}|{uri1} {fragment2} {ahash}|{uri3} {fragment4}'.format(
                fragment2=_Fragment(uri=uri2, hash=ahash).asEncodedString(),
                fragment4=_Fragment(uri=uri4, hash=ahash).asEncodedString(),
                **locals())
        result = fixEncodedFragments(data)
        self.assertFalse('|' in result)
        fragments = [_Fragment.fromEncodedString(s) for s in result.split(' ')]
        self.assertEquals([uri1, uri2, uri3, uri4], [f.uri for f in fragments])

    def _newPlein(self, storageLabel="storage", oaiAddRecordLabel="oaiJazz"):
        return Plein(directory=self.tempdir, storageLabel=storageLabel, oaiAddRecordLabel=oaiAddRecordLabel, rdfxsdUrl='http://example.org/rdf.xsd')

def createRdfNode(aboutUri):
    root = XML("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
<rdf:Description rdf:about="%s" xmlns:dcterms="http://purl.org/dc/terms/"></rdf:Description></rdf:RDF>""" % aboutUri).getroottree()
    return root, root.getroot().getchildren()[0]
