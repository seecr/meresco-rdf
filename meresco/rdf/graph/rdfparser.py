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


from urlparse import urljoin as urijoin

from lxml.etree import Element

from meresco.xml import namespaces

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
- rdf:li
- rdf:bagID
- rdf:aboutEach
- rdf:aboutEachPrefix
- reification (hence rdf:ID is only recognized as abbreviated URI)
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
        if e.attrib.keys() in ([], [rdf_ID_tag]):
            obj = Literal(e.text or '', lang=e.attrib.get(x_lang_tag))
            self.addTriple(subj, uri, obj)
        else:
            if rdf_resource_tag in e.attrib:
                r = Uri(urijoin(e.base, e.attrib[rdf_resource_tag]))
            else:
                nodeID = None
                if rdf_nodeID_tag in e.attrib:
                    nodeID = e.attrib[rdf_nodeID_tag]
                r = self.bNode(nodeID=nodeID)

            for attrib, value in filter(lambda (k, v): k not in DISALLOWED, e.attrib.items()):
                if attrib != rdf_type_tag:
                    o = Literal(value, lang=e.attrib.get(x_lang_tag))
                    self.addTriple(r.value, self.uriForTag(attrib), o)
                else:
                    self.addTriple(r.value, rdf_type_uri, Uri(value))
            self.addTriple(subj, uri, r)

    def resourcePropertyElt(self, subj, e, n):
        uri = self.uriForTag(e.tag)
        childSubj = self.nodeElement(n)
        self.addTriple(subj, uri, childSubj)

    def literalPropertyElt(self, subj, e, eText):
        uri = self.uriForTag(e.tag)
        o = Literal(eText, lang=e.attrib.get(x_lang_tag))  # TODO: process datatype with e.attrib.get(rdf_datatype_tag
        self.addTriple(subj, uri, o)

    def parseTypeResourcePropertyElt(self, subj, e, children):
        uri = self.uriForTag(e.tag)
        node = self.bNode()
        self.addTriple(subj, uri, node)
        for child in children:
            self.propertyElt(node.value, child)


def getText(node):
    # *Only* call with an Element
    allText = node.text or ''

    for c in node.getchildren():
        tail = c.tail
        if tail:
            allText += tail

    return allText or None


x_lang_tag = namespaces.curieToTag("xml:lang")
rdf_RDF_tag = namespaces.curieToTag("rdf:RDF")
rdf_ID_tag = namespaces.curieToTag("rdf:ID")
rdf_about_tag = namespaces.curieToTag("rdf:about")
rdf_aboutEach_tag = namespaces.curieToTag("rdf:aboutEach")
rdf_aboutEachPrefix_tag = namespaces.curieToTag("rdf:aboutEachPrefix")
rdf_type_tag = namespaces.curieToTag("rdf:type")
rdf_resource_tag = namespaces.curieToTag("rdf:resource")
rdf_Description_tag = namespaces.curieToTag("rdf:Description")
rdf_bagID_tag = namespaces.curieToTag("rdf:bagID")
rdf_parseType_tag = namespaces.curieToTag("rdf:parseType")
rdf_nodeID_tag = namespaces.curieToTag("rdf:nodeID")
rdf_datatype_tag = namespaces.curieToTag("rdf:datatype")
rdf_li_tag = namespaces.curieToTag("rdf:li")
rdf_type_uri = namespaces.curieToUri('rdf:type')

DISALLOWED = set([rdf_RDF_tag, rdf_ID_tag, rdf_about_tag, rdf_bagID_tag,
    rdf_parseType_tag, rdf_resource_tag, rdf_nodeID_tag, rdf_datatype_tag,
    rdf_li_tag, rdf_aboutEach_tag, rdf_aboutEachPrefix_tag])

