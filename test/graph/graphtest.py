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

from meresco.xml.namespaces import curieToUri
from meresco.rdf.graph import Graph, Literal, Uri, BNode

from seecr.test import SeecrTestCase


class GraphTest(SeecrTestCase):
    def testGraph(self):
        g = Graph()
        g.addTriple('x', 'y', 'z')
        g.addTriple(subject='a', predicate='b', object='c')
        self.assertEquals([('x', 'y', 'z'), ('a', 'b', 'c')], list(g.triples()))

        # 'x', 'y', 'z'  -->       # 000
        g.addTriple('x', 'y', '3') # 001
        g.addTriple('x', '2', 'z') # 010
        g.addTriple('x', '2', '3') # 011
        g.addTriple('1', 'y', 'z') # 100
        g.addTriple('1', 'y', '3') # 101
        g.addTriple('1', '2', 'z') # 110
        g.addTriple('1', '2', '3') # 111

        self.assertEquals([('x', 'y', 'z')], sorted(g.triples('x', 'y', 'z')))
        self.assertEquals([('x', 'y', 'z')], sorted(g.triples(subject='x', predicate='y', object='z')))
        self.assertEquals([('x', 'y', '3'), ('x', 'y', 'z')], sorted(g.triples('x', 'y', None)))
        self.assertEquals([('x', '2', 'z'), ('x', 'y', 'z')], sorted(g.triples('x', None, 'z')))
        self.assertEquals([('x', '2', '3'), ('x', '2', 'z'), ('x', 'y', '3'), ('x', 'y', 'z')], sorted(g.triples('x', None, None)))
        self.assertEquals([('1', 'y', 'z'), ('x', 'y', 'z')], sorted(g.triples(None, 'y', 'z')))
        self.assertEquals([('1', 'y', '3'), ('1', 'y', 'z'), ('x', 'y', '3'), ('x', 'y', 'z')], sorted(g.triples(None, 'y', None)))
        self.assertEquals([('1', '2', 'z'), ('1', 'y', 'z'), ('x', '2', 'z'), ('x', 'y', 'z')], sorted(g.triples(None, None, 'z')))
        self.assertEquals(sorted(g.triples()), sorted(g.triples(None, None, None)))
        self.assertEquals(9, len(list(g.triples())))

        # objects()
        self.assertEquals(['3', 'z'], sorted(g.objects(subject='x', predicate='y')))

    def testRemoveTriple(self):
        g = Graph()
        g.addTriple(subject='u:ri', predicate='p:redicate', object='obj')
        g.addTriple(subject='u:ri', predicate='p:redicate', object='obj2')

        self.assertEquals(2, len(list(g.triples())))
        self.assertEquals(12, len(g._tripleDict))  # Whitebox no-leaking defaultdict entries on delete

        g.removeTriple(subject='u:ri', predicate='p:redicate', object='obj2')

        self.assertEquals(8, len(g._tripleDict))  # Whitebox no-leaking defaultdict entries on delete

        # Keep 1
        self.assertEquals(1, len(list(g.triples())))
        self.assertEquals(1, len(list(g.triples(None, None, None))))
        self.assertEquals(1, len(list(g.triples(None, None, 'obj'))))
        self.assertEquals(1, len(list(g.triples(None, 'p:redicate', None))))
        self.assertEquals(1, len(list(g.triples(None, 'p:redicate', 'obj'))))
        self.assertEquals(1, len(list(g.triples('u:ri', None, None))))
        self.assertEquals(1, len(list(g.triples('u:ri', None, 'obj'))))
        self.assertEquals(1, len(list(g.triples('u:ri', 'p:redicate', None))))
        self.assertEquals(1, len(list(g.triples('u:ri', 'p:redicate', 'obj'))))

        # Kill 1
        self.assertEquals(0, len(list(g.triples(None, None, 'obj2'))))
        self.assertEquals(0, len(list(g.triples(None, 'p:redicate', 'obj2'))))
        self.assertEquals(0, len(list(g.triples('u:ri', 'p:redicate', 'obj2'))))

    def testRemoveTripleOfNonExistingDoesNotLeak(self):
        g = Graph()

        self.assertEquals(0, len(list(g.triples())))
        self.assertEquals(0, len(g._tripleDict))  # Whitebox no-leaking defaultdict entries on delete

        g.removeTriple(subject='u:ri', predicate='p:redicate', object='obj2')

        self.assertEquals(0, len(g._tripleDict))  # Whitebox no-leaking defaultdict entries on delete

    def testGraphContains(self):
        g = Graph()
        g.addTriple('u:ri', 'p:redicate', 'obj')
        self.assertTrue(('u:ri', 'p:redicate', 'obj') in g)
        self.assertTrue(('u:ri', 'p:redicate', None) in g)
        self.assertTrue(('u:ri', None, 'obj') in g)
        self.assertTrue(('u:ri', None, None) in g)
        self.assertTrue((None, 'p:redicate', 'obj') in g)
        self.assertTrue((None, 'p:redicate', None) in g)
        self.assertTrue((None, None, 'obj') in g)
        self.assertTrue((None, None, None) in g)
        self.assertFalse(('U:ri', 'p:redicate', 'obj') in g)
        self.assertFalse(('u:ri', 'P:redicate', 'obj') in g)
        self.assertFalse(('u:ri', 'p:redicate', 'Obj') in g)

        # Same for Uri/Literal/BNode
        g = Graph()
        g.addTriple('u:ri', 'p:redicate', Uri('o:bj'))
        self.assertTrue(('u:ri', 'p:redicate', Uri('o:bj')) in g)
        self.assertTrue((None, 'p:redicate', Uri('o:bj')) in g)
        self.assertTrue(('u:ri', 'p:redicate', None) in g)
        self.assertFalse(('u:ri', 'p:redicate', Uri('O:bj')) in g)

        g = Graph()
        g.addTriple('u:ri', 'p:redicate', BNode('_:42'))
        self.assertTrue(('u:ri', 'p:redicate', BNode('_:42')) in g)
        self.assertTrue((None, 'p:redicate', BNode('_:42')) in g)
        self.assertTrue(('u:ri', 'p:redicate', None) in g)
        self.assertFalse(('u:ri', 'p:redicate', BNode('_:666')) in g)

        g = Graph()
        g.addTriple('u:ri', 'p:redicate', Literal('obj', lang='en'))
        self.assertTrue(('u:ri', 'p:redicate', Literal('obj', lang='en')) in g)
        self.assertTrue((None, 'p:redicate', Literal('obj', lang='en')) in g)
        self.assertTrue(('u:ri', 'p:redicate', None) in g)
        self.assertFalse(('u:ri', 'p:redicate', Literal('Obj', lang='en')) in g)
        # Also false, different lang or datatype (**no guessing**, inspect triples & compare yourself if thats your game).
        self.assertFalse(('u:ri', 'p:redicate', Literal('obj', lang='nl')) in g)
        self.assertFalse(('u:ri', 'p:redicate', Literal('obj')) in g)

    def testGraphFindLabel(self):
        g = Graph()
        g.addTriple('u:ri', curieToUri('rdfs:label'), Literal('rdfsLabel'))
        self.assertEquals(Literal('rdfsLabel'), g.findLabel(uri='u:ri'))

        g.addTriple('u:ri', curieToUri('rdfs:label'), Literal('rdfsLabelEN', lang='en'))
        self.assertEquals(Literal('rdfsLabelEN', lang='en'), g.findLabel(uri='u:ri'))

        g.addTriple('u:ri', curieToUri('skos:prefLabel'), Literal('skosPrefLabel'))
        self.assertEquals(Literal('rdfsLabelEN', lang='en'), g.findLabel(uri='u:ri'))

        g.addTriple('u:ri', curieToUri('skos:prefLabel'), Literal('skosPrefLabelNL', lang='nl'))
        self.assertEquals(Literal('skosPrefLabelNL', lang='nl'), g.findLabel(uri='u:ri'))

        g.addTriple('u:ri', curieToUri('rdfs:label'), Literal('rdfsLabelNL', lang='nl'))
        self.assertEquals(Literal('rdfsLabelNL', lang='nl'), g.findLabel(uri='u:ri'))

        g.addTriple('u:ri', curieToUri('foaf:name'), Literal('foafNameNL', lang='nl'))
        self.assertEquals(Literal('foafNameNL', lang='nl'), g.findLabel(uri='u:ri'))

    def testGraphFindLabelSpecifyAllowedLabelPredicates(self):
        g = Graph()
        g.addTriple('u:ri', curieToUri('rdfs:label'), Literal('rdfsLabel'))
        self.assertEquals(None, g.findLabel(uri='u:ri', labelPredicates=[]))
        self.assertEquals(Literal('rdfsLabel'), g.findLabel(uri='u:ri', labelPredicates=[curieToUri('rdfs:label')]))

        g.addTriple('u:ri2', curieToUri('skos:altLabel'), Literal('altLabel'))
        self.assertEquals(None, g.findLabel(uri='u:ri2', labelPredicates=[curieToUri('rdfs:label')]))
        self.assertEquals(Literal('altLabel'), g.findLabel(uri='u:ri2', labelPredicates=[curieToUri('rdfs:label'), curieToUri('skos:altLabel')]))

    def testMatchTriplePathRealRdfTriples(self):
        # Note: at the moment we follow the convention that only (for performance reasons) the triple's object is wrapped in Literal, Uri or BNode.
        # All variable bindings get wrapped.
        g = Graph()
        g.addTriple('uri:x', 'uri:y', Uri('uri:z'))
        g.addTriple('uri:a', 'uri:b', Literal('c'))
        g.addTriple('uri:z', 'uri:d', Uri('uri:a'))
        g.addTriple('uri:a', 'uri:e', Uri('uri:x'))

        self.assertEquals(
            [{'v': Uri('uri:x')}],
            list(g.matchTriplePatterns(('?v', 'uri:y', Uri('uri:z')))))
        self.assertEquals(
            [{'v': Uri('uri:a')}],
            list(g.matchTriplePatterns(('?v', 'uri:b', None))))
        self.assertEquals(
            [{'v': Uri('uri:a')}, {'v': Uri('uri:x')}, {'v': Uri('uri:z')}],
            sorted(g.matchTriplePatterns((None, None, '?v'), ('?v', None, None))))
        self.assertEquals(
            [{'v': Uri('uri:a')}, {'v': Uri('uri:x')}, {'v': Uri('uri:z')}],
            sorted(g.matchTriplePatterns(('?v', None, None), (None, None, '?v'))))
        self.assertEquals(
            [dict(v0=Uri('uri:a'), v1=Uri('uri:x'), v2=Uri('uri:z'))],
            list(g.matchTriplePatterns(
                ('?v0', None, '?v1'),
                ('?v1', None, '?v2'),
                ('?v2', None, '?v0'),
                ('?v0', None, Literal('c')))))
