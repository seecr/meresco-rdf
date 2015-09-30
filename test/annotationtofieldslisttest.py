# -*- coding: utf-8 -*-
## begin license ##
#
# "Meresco Distributed" has components for group management based on "Meresco Components."
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
#
# This file is part of "Meresco Distributed"
#
# "Meresco Distributed" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Distributed" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Distributed"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from lxml.etree import XML

from weightless.core import consume

from seecr.test import SeecrTestCase, CallTrace

from meresco.rdf.annotationtofieldslist import AnnotationToFieldsList
from meresco.xml import namespaces


class AnnotationToFieldsListTest(SeecrTestCase):
    def testFieldsFromSummaryAnnotation(self):
        self._createAnnotationToFieldsList()
        consume(self.annotationTofieldslist.add(lxmlNode=XML(ANNOTATION_SUMMARIZING)))
        fields = self. observer.calledMethods[0].kwargs['fieldslist']
        self.assertEquals([
                ('oa:annotatedBy.uri', "http://data.bibliotheek.nl/id/bnl"),
                ('oa:motivatedBy.uri', "http://data.bibliotheek.nl/ns/nbc/oa#summarizing"),
                ('oa:hasTarget.uri', "http://data.bibliotheek.nl/ggc/ppn/78240829X"),
                ('rdf:type.uri', "http://dbpedia.org/ontology/Book"),
                ('dcterms:type.uri', "http://dbpedia.org/ontology/Book"),
                ('dcterms:title', 'De Båèrkểnhuizen, Anno 1349'),
                ('dcterms:identifier.uri', 'http://data.bibliotheek.nl/ggc/ppn/78240829X'),
                ('dcterms:creator', 'Nieuwkerk Kramer, H G'),
                ('dcterms:creator.uri', 'http://data.bibliotheek.nl/ggc/ppn/987'),
                ('dcterms:creator.rdfs:label', 'Some Author'),
                ('dcterms:date', '1966'),
                ('dcterms:language.uri', 'urn:iso:std:iso:639:-2:dut'),
                ('dcterms:language.rdfs:label', 'Nederlands'),
                ('dcterms:extent', '15 p'),
                ('dcterms:isFormatOf.uri', "urn:a:work:123"),
                ('skos:note', 'BQM_14'),
                ('dcterms:spatial.uri', 'http://data.bibliotheek.nl/uitburo/location/8e71243e-abb0-407b-83a1-303db1f676e0'),
                ('dcterms:spatial.rdfs:label', 'Museum Boerhaave'),
                ('dcterms:spatial.geo:lat', '52.1613636'),
                ('dcterms:spatial.geo:long', '4.4891784'),
                ('dcterms:spatial.vcard:region', 'Leiden')
            ], fields)


    def testOnlyFieldsMatchingFilter(self):
        self._createAnnotationToFieldsList(filterFields={"dcterms:title":{'max_length': 10}, "rdf:type.uri":{}})
        consume(self.annotationTofieldslist.add(lxmlNode=XML(ANNOTATION_SUMMARIZING)))
        fields = self. observer.calledMethods[0].kwargs['fieldslist']
        self.assertEquals([
                ('rdf:type.uri', "http://dbpedia.org/ontology/Book"),
                ('dcterms:title', 'De Båèrkển'),
            ], fields)


    def _createAnnotationToFieldsList(self, **kwargs):
        self.annotationTofieldslist = AnnotationToFieldsList(namespaces=namespaces, **kwargs)
        self.observer = CallTrace(emptyGeneratorMethods=['add'])
        self.annotationTofieldslist.addObserver(self.observer)


ANNOTATION_SUMMARIZING = """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<oa:Annotation xmlns:oa="http://www.w3.org/ns/oa#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" rdf:about="http://data.bibliotheek.nl/nbc/summary#a7c42194d70564da62e2f184a9c488298fd1493d">
    <oa:annotatedBy rdf:resource="http://data.bibliotheek.nl/id/bnl"/>
    <oa:motivatedBy rdf:resource="http://data.bibliotheek.nl/ns/nbc/oa#summarizing"/>
    <oa:hasTarget rdf:resource="http://data.bibliotheek.nl/ggc/ppn/78240829X"/>
    <oa:hasBody>
      <rdf:Description xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:skos="%(skos)s" xmlns:geo="%(geo)s" xmlns:vcard="%(vcard)s">
        <rdf:type rdf:resource="http://dbpedia.org/ontology/Book"/>
        <dcterms:type rdf:resource="http://dbpedia.org/ontology/Book"/>
        <dcterms:title>De Båèrkểnhuizen, Anno 1349</dcterms:title>
        <dcterms:identifier rdf:resource="http://data.bibliotheek.nl/ggc/ppn/78240829X"/>
        <dcterms:creator>Nieuwkerk Kramer, H G</dcterms:creator>
        <dcterms:creator>
            <rdf:Description rdf:about="http://data.bibliotheek.nl/ggc/ppn/987">
                <rdfs:label>Some Author</rdfs:label>
            </rdf:Description>
        </dcterms:creator>
        <dcterms:date>1966</dcterms:date>
        <dcterms:language>
          <rdf:Description rdf:about="urn:iso:std:iso:639:-2:dut">
            <rdfs:label>Nederlands</rdfs:label>
          </rdf:Description>
        </dcterms:language>
        <dcterms:extent>15 p</dcterms:extent>
        <dcterms:isFormatOf rdf:resource="urn:a:work:123"/>
        <skos:note>BQM_14</skos:note>
        <dcterms:spatial>
          <rdf:Description rdf:about="http://data.bibliotheek.nl/uitburo/location/8e71243e-abb0-407b-83a1-303db1f676e0">
            <rdfs:label>Museum Boerhaave</rdfs:label>
            <geo:lat>52.1613636</geo:lat>
            <geo:long>4.4891784</geo:long>
            <vcard:region>Leiden</vcard:region>
          </rdf:Description>
        </dcterms:spatial>
      </rdf:Description>
    </oa:hasBody>
  </oa:Annotation>
</rdf:RDF>""" % namespaces