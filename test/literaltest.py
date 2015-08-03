## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2011-2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from seecr.test import SeecrTestCase

from meresco.rdf import Literal, Uri


class LiteralTest(SeecrTestCase):
    def testInstantiate(self):
        self.assertEquals('Li-ter-al', str(Literal('Li-ter-al')))
        self.assertEquals("'Li-ter-al'@nl", str(Literal('Li-ter-al', lang='nl')))
        self.assertEquals("Literal('Li-ter-al')", repr(Literal('Li-ter-al')))
        self.assertEquals("Literal('Li-ter-al', lang='nl')", repr(Literal('Li-ter-al', lang='nl')))

    def testHashForCollections(self):
        l1 = Literal('u:ri', lang='nl')
        l2 = Literal('u:ri', lang='nl')
        self.assertEquals(l1, l2)
        self.assertEquals(hash(l1), hash(l2))
        coll = set([l1, l2])
        self.assertEquals(1, len(coll))

        self.assertNotEqual(hash(l1), hash(Literal('u:ri', lang='en')))
        self.assertNotEqual(hash(l1), hash(Literal('U:RI', lang='nl')))

    def testOnlyStringLikeObjects(self):
        self.assertRaises(ValueError, lambda: Literal(42))
        self.assertRaises(ValueError, lambda: Literal(object()))
        self.assertEquals('u:ri', str(Literal('u:ri')))
        self.assertEquals('u:ri', str(Literal(u'u:ri')))

        # Re-wrapping Literal (or Uri) disallowed
        self.assertRaises(ValueError, lambda: Literal(Literal('u:ri')))
        self.assertRaises(ValueError, lambda: Literal(Uri('u:ri')))

    def testWithoutLang(self):
        l = Literal.fromDict({"type": "literal", "value": "http://www.rnaproject.org/data/rnax/odw/InformationConcept"})
        self.assertEquals("http://www.rnaproject.org/data/rnax/odw/InformationConcept", l.value)
        self.assertEquals(None, l.lang)

    def testWithLang(self):
        l = Literal.fromDict({"type": "literal", "xml:lang": "eng", "value": "http://www.rnaproject.org/data/rnax/odw/InformationConcept"})
        self.assertEquals("http://www.rnaproject.org/data/rnax/odw/InformationConcept", l.value)
        self.assertEquals("eng", l.lang)

    def testEquals(self):
        l1 = Literal.fromDict({"type": "literal", "xml:lang": "eng", "value": "VALUE"})
        l2 = Literal.fromDict({"type": "literal", "xml:lang": "eng", "value": "VALUE"})
        self.assertEquals(l1, l2)

        l2 = Literal.fromDict({"type": "literal", "xml:lang": "dut", "value": "VALUE"})
        self.assertNotEqual(l1, l2)

        l2 = Literal.fromDict({"type": "literal", "value": "VALUE"})
        self.assertNotEqual(l1, l2)

        l2 = Literal.fromDict({"type": "literal", "value": "OTHER VALUE"})
        self.assertNotEqual(l1, l2)
