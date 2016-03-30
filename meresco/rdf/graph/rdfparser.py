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


from urlparse import urljoin as urijoin

from lxml.etree import Element

from meresco.xml.namespaces import curieToTag, curieToUri

from .uri import Uri
from .bnode import BNode
from .literal import Literal
from .graph import Graph


# lxml-modification of code taken from http://infomesh.net/2003/rdfparser/rdfxml.py.txt by Sean B. Palmer
class RDFParser(object):
    """Please note that this is currently by no means a feature complete RDF/XML parser!

Particularly the following RDF/XML constructs are not supported:
- rdf:datatype (!)
- rdf:parseType "Literal" and "Collection"
- rdf:li (generated node ids)
- rdf:bagID
- rdf:aboutEach
- rdf:aboutEachPrefix
- implicit base

Input is not validated in any way.
How incorrect RDF/XML (or input with unsupported constructs) is parsed into a graph remains undefined.
"""

    _element2uri = {}

    def __init__(self, sink=None):
        self._sink = sink or Graph()
        self.addTriple = self._sink.addTriple

    def parse(self, lxmlNode):
        root = lxmlNode
        if hasattr(lxmlNode, 'getroot'):
            root = lxmlNode.getroot()
        if root.tag == rdf_RDF_tag:
            for child in root.iterchildren(tag=Element):
                self.nodeElement(child)
        else:
            self.nodeElement(root)
        return self._sink

    def bNode(self, nodeID=None):
        if not nodeID is None:
            if not nodeID[0].isalpha(): nodeID = 'b' + nodeID
            return BNode('_:' + nodeID)
        return BNode()

    @classmethod
    def uriForTag(cls, tag):
        try:
            uri = cls._element2uri[tag]
        except KeyError:
            uri = cls._element2uri[tag] = ''.join(tag[1:].split('}'))
        return uri

    def nodeElement(self, e):
        # *Only* call with an Element
        if rdf_about_tag in e.attrib:
            subj = Uri(urijoin(e.base, e.attrib[rdf_about_tag]))
        elif rdf_ID_tag in e.attrib:
            subj = Uri(urijoin(e.base, '#' + e.attrib[rdf_ID_tag]))
        else:
            nodeID = None
            if rdf_nodeID_tag in e.attrib:
                nodeID = e.attrib[rdf_nodeID_tag]
            subj = self.bNode(nodeID=nodeID)

        if e.tag != rdf_Description_tag:
            self.addTriple(subj.value, rdf_type_uri, Uri(self.uriForTag(e.tag)))
        if rdf_type_tag in e.attrib:
            self.addTriple(subj.value, rdf_type_uri, Uri(e.attrib[rdf_type_tag]))
        for attr, value in e.attrib.items():
            if attr not in DISALLOWED and attr != rdf_type_tag:
                objt = Literal(value, lang=e.attrib.get(x_lang_tag))
                self.addTriple(subj.value, self.uriForTag(attr), objt)

        for element in e.iterchildren(tag=Element):
            self.propertyElt(subj.value, element)
        return subj

    def propertyElt(self, subj, e):
        children = [c for c in e.iterchildren(tag=Element)]
        eText = getText(e)
        if len(children) == 0 and eText:
            self.literalPropertyElt(subj, e, eText)
        elif len(children) == 1 and not rdf_parseType_tag in e.attrib:
            self.resourcePropertyElt(subj, e, children[0])
        elif 'Resource' == e.attrib.get(rdf_parseType_tag):
            self.parseTypeResourcePropertyElt(subj, e, children)
        elif not eText:
            self.emptyPropertyElt(subj, e)

    def emptyPropertyElt(self, subj, e):
        uri = self.uriForTag(e.tag)
        if sum(1 for k in e.attrib.keys() if not k == rdf_ID_tag) == 0:
            obj = Literal(e.text or '', lang=e.attrib.get(x_lang_tag))
        else:
            resource = e.attrib.get(rdf_resource_tag)
            if not resource is None:
                obj = Uri(urijoin(e.base, resource))
            else:
                obj = self.bNode(nodeID=e.attrib.get(rdf_nodeID_tag))
            for attrib, value in filter(lambda (k, v): k not in DISALLOWED, e.attrib.items()):
                if attrib != rdf_type_tag:
                    self.addTriple(obj.value, self.uriForTag(attrib), Literal(value, lang=e.attrib.get(x_lang_tag)))
                else:
                    self.addTriple(obj.value, rdf_type_uri, Uri(value))
        self.addTriple(subj, uri, obj)
        rdfID = e.attrib.get(rdf_ID_tag)
        if not rdfID is None:
            self.reify(subj, uri, obj, e.base, rdfID)

    def resourcePropertyElt(self, subj, e, n):
        uri = self.uriForTag(e.tag)
        childSubj = self.nodeElement(n)
        self.addTriple(subj, uri, childSubj)
        rdfID = e.attrib.get(rdf_ID_tag)
        if not rdfID is None:
            self.reify(subj, uri, childSubj, e.base, rdfID)

    def literalPropertyElt(self, subj, e, eText):
        uri = self.uriForTag(e.tag)
        o = Literal(eText, lang=e.attrib.get(x_lang_tag))  # TODO: process datatype with e.attrib.get(rdf_datatype_tag
        self.addTriple(subj, uri, o)
        rdfID = e.attrib.get(rdf_ID_tag)
        if not rdfID is None:
            self.reify(subj, uri, o, e.base, rdfID)

    def parseTypeResourcePropertyElt(self, subj, e, children):
        uri = self.uriForTag(e.tag)
        node = self.bNode()
        self.addTriple(subj, uri, node)
        rdfID = e.attrib.get(rdf_ID_tag)
        if not rdfID is None:
            self.reify(subj, uri, node, e.base, rdfID)
        for child in children:
            self.propertyElt(node.value, child)

    def reify(self, s, p, o, base, rdfID):
        r = urijoin(base, '#' + rdfID)
        self.addTriple(r, rdf_subject_uri, Uri(s))
        self.addTriple(r, rdf_predicate_uri, Uri(p))
        self.addTriple(r, rdf_object_uri, o)
        self.addTriple(r, rdf_type_uri, Uri(rdf_Statement_uri))


def getText(node):
    # *Only* call with an Element
    allText = node.text or ''

    for c in node.getchildren():
        tail = c.tail
        if tail:
            allText += tail

    return allText or None


x_lang_tag = curieToTag("xml:lang")
rdf_RDF_tag = curieToTag("rdf:RDF")
rdf_ID_tag = curieToTag("rdf:ID")
rdf_about_tag = curieToTag("rdf:about")
rdf_aboutEach_tag = curieToTag("rdf:aboutEach")
rdf_aboutEachPrefix_tag = curieToTag("rdf:aboutEachPrefix")
rdf_type_tag = curieToTag("rdf:type")
rdf_resource_tag = curieToTag("rdf:resource")
rdf_Description_tag = curieToTag("rdf:Description")
rdf_bagID_tag = curieToTag("rdf:bagID")
rdf_parseType_tag = curieToTag("rdf:parseType")
rdf_nodeID_tag = curieToTag("rdf:nodeID")
rdf_datatype_tag = curieToTag("rdf:datatype")
rdf_li_tag = curieToTag("rdf:li")

rdf_Statement_uri = curieToUri('rdf:Statement')
rdf_type_uri = curieToUri('rdf:type')
rdf_subject_uri = curieToUri('rdf:subject')
rdf_predicate_uri = curieToUri('rdf:predicate')
rdf_object_uri = curieToUri('rdf:object')


DISALLOWED = set([rdf_RDF_tag, rdf_ID_tag, rdf_about_tag, rdf_bagID_tag,
    rdf_parseType_tag, rdf_resource_tag, rdf_nodeID_tag, rdf_datatype_tag,
    rdf_li_tag, rdf_aboutEach_tag, rdf_aboutEachPrefix_tag])

