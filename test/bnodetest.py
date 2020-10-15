## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2011-2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from meresco.rdf import Uri, Literal, BNode


class BNodeTest(SeecrTestCase):
    def testCreate(self):
        bnode = BNode.fromDict({"type": "bnode", "value": "node12345"})
        self.assertNotEqual("node12345", bnode)
        self.assertEqual("node12345", str(bnode))
        self.assertEqual(bnode, BNode('node12345'))

    def testHashForCollections(self):
        bnode1 = BNode('node12345')
        bnode2 = BNode('node12345')
        self.assertEqual(bnode1, bnode2)
        self.assertEqual(hash(bnode1), hash(bnode2))
        coll = set([bnode1, bnode2])
        self.assertEqual(1, len(coll))
        self.assertNotEqual(hash(bnode1), hash(BNode('NODE12345')))

    def testOnlyStringLikeObjects(self):
        self.assertRaises(ValueError, lambda: BNode(42))
        self.assertRaises(ValueError, lambda: BNode(object()))
        self.assertEqual('node12345', str(BNode('node12345')))
        self.assertEqual('node12345', str(BNode('node12345')))

        # Re-wrapping Uri (or Literal) disallowed
        self.assertRaises(ValueError, lambda: BNode(BNode('node12345')))
        self.assertRaises(ValueError, lambda: BNode(Uri('u:ri')))
        self.assertRaises(ValueError, lambda: BNode(Literal('x')))
