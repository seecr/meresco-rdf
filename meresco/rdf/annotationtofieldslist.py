## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from lxml.etree import _ElementTree, _Comment

from weightless.core import compose
from meresco.core import Observable

from meresco.xml import namespaces


class AnnotationToFieldsList(Observable):
    def __init__(self, filterFields=None, namespaces=namespaces, **kwargs):
        """
            Creates AnnotationToFieldsList with possibility to filter fields and modify values.

            Example filtering only title and subject (max 10 length) fields:
            filterFields = {
                'title': {},
                'subject': {'max_length': 10},
            }
        """
        Observable.__init__(self, **kwargs)
        if filterFields:
            _filterFields = dict((fieldname, _valueMethod(**restrictions))
                for fieldname, restrictions in filterFields.items())
            self._modifyField = lambda fieldname, value: (fieldname, _filterFields.get(fieldname, lambda value: None)(value))
        else:
            self._modifyField = lambda fieldname, value: (fieldname, value)
        self._namespaces = namespaces

    def add(self, lxmlNode, **kwargs):
        if type(lxmlNode) is _ElementTree:
            lxmlNode = lxmlNode.getroot()
        fieldslist = list(self.fieldsFromAnnotation(lxmlNode))
        yield self.all.add(fieldslist=fieldslist, **kwargs)

    def fieldsFromAnnotation(self, lxmlNode):
        return ((fieldname, value) for fieldname, value in compose(self._fieldsFromAnnotation(lxmlNode)) if value is not None)

    def _fieldsFromAnnotation(self, lxmlNode):
        annotation = lxmlNode.getchildren()[0]
        for child in annotation.iterchildren():
            fieldname = self._namespaces.tagToCurie(child.tag)
            if child.tag != HAS_BODY:
                yield self._modifyField(fieldname + ".uri", child.attrib.get(RDF_RESOURCE))
            else:
                bodyNode = child.getchildren()[0]
                for bodyChildNode in bodyNode.iterchildren():
                    if not isinstance(bodyChildNode, _Comment):
                        yield self._yieldField(bodyChildNode)

    def _yieldField(self, node, parent=''):
        fieldname = self._namespaces.tagToCurie(node.tag)
        if fieldname != 'rdf:Description' and (fieldname != 'rdf:type' or not parent):
            if parent:
                parent += "."
            fieldname = parent + fieldname
        else:
            fieldname = parent

        for name, value in (
                ('.uri', node.attrib.get(RDF_RESOURCE)),
                ('.uri', node.attrib.get(RDF_ABOUT)),
                ('', node.text)
            ):
            if value is None or value.strip() == '':
                continue
            yield self._modifyField(fieldname + name, value)
        for child in node.iterchildren():
            yield self._yieldField(child, parent=fieldname)

def _valueMethod(max_length=None):
    if max_length:
        return lambda value: None if value is None else value[:max_length]
    return lambda value: value

RDF_RESOURCE = namespaces.curieToTag('rdf:resource')
RDF_ABOUT = namespaces.curieToTag('rdf:about')
IS_FORMAT_OF = namespaces.curieToTag('dcterms:isFormatOf')
MOTIVATED_BY = namespaces.curieToTag('oa:motivatedBy')
HAS_TARGET = namespaces.curieToTag('oa:hasTarget')
HAS_BODY = namespaces.curieToTag('oa:hasBody')
