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

from meresco.rdf import Uri, Literal


class UriTest(SeecrTestCase):
    def testCreate(self):
        u = Uri.fromDict({"type": "uri", "value": "http://www.rnaproject.org/data/rnax/odw/InformationConcept"})
        self.assertNotEquals("http://www.rnaproject.org/data/rnax/odw/InformationConcept", u)
        self.assertEquals("http://www.rnaproject.org/data/rnax/odw/InformationConcept", str(u))
        self.assertEquals(u, Uri('http://www.rnaproject.org/data/rnax/odw/InformationConcept'))

    def testHashForCollections(self):
        uri1 = Uri('u:ri')
        uri2 = Uri('u:ri')
        self.assertEquals(uri1, uri2)
        self.assertEquals(hash(uri1), hash(uri2))
        coll = set([uri1, uri2])
        self.assertEquals(1, len(coll))

        self.assertNotEqual(hash(uri1), hash(Uri('U:RI')))

    def testOnlyStringLikeObjects(self):
        self.assertRaises(ValueError, lambda: Uri(42))
        self.assertRaises(ValueError, lambda: Uri(object()))
        self.assertEquals('u:ri', str(Uri('u:ri')))
        self.assertEquals('u:ri', str(Uri(u'u:ri')))

        # Re-wrapping Uri (or Literal) disallowed
        self.assertRaises(ValueError, lambda: Uri(Uri('u:ri')))
        self.assertRaises(ValueError, lambda: Uri(Literal('u:ri')))

