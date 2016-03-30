## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os.path import join
from collections import defaultdict
from copy import deepcopy
from hashlib import sha1
from lxml.etree import Element, SubElement, ElementTree, XML, cleanup_namespaces, tostring

from weightless.core import Yield
from meresco.core import Observable

from meresco.lucene.lucenekeyvaluestore import LuceneKeyValueStore
from base64 import b64decode, b64encode

from meresco.xml.namespaces import namespaces, xpath, xpathFirst, curieToTag

import sys


class Plein(Observable):
    def __init__(self, directory, storageLabel, oaiAddRecordLabel, rdfxsdUrl=None, name=None):
        Observable.__init__(self, name=name)
        self._fragmentAdmin = LuceneKeyValueStore(join(directory, 'fragmentAdmin'))
        self._storageLabel = storageLabel
        self._oaiAddRecordLabel = oaiAddRecordLabel
        self._rdfxsdUrl = rdfxsdUrl or ''

    def add(self, identifier, lxmlNode, oaiArgs=None, **kwargs):
        rdfNode = xpathFirst(lxmlNode, '/rdf:RDF')
        if rdfNode is None:
            raise ValueError("Expected lxmlNode with xpath '/rdf:RDF'")
        rdfNode = ElementTree(rdfNode)
        yield self._add(recordId=str(identifier), fragments=self._extractFragments(rdfNode), oaiArgs=oaiArgs)

    def delete(self, identifier):
        yield self._delete(recordId=str(identifier))

    def commit(self):
        self._fragmentAdmin.commit()

    def close(self):
        self._fragmentAdmin.close()

    def handleShutdown(self):
        print 'handle shutdown: saving plein'
        from sys import stdout; stdout.flush()
        self.close()

    def _extractFragments(self, lxmlNode):
        fragments = {}
        for (fragmentNode, uri) in self._findFragmentNodesWithAboutUris(lxmlNode):
            fragment = _Fragment(uri, lxmltostringUtf8(self._normalizeRdfDescription(fragmentNode)))
            fragments[fragment.hash] = fragment
        return fragments

    def _findFragmentNodesWithAboutUris(self, lxmlNode):
        for descriptionNode in xpath(lxmlNode, "*[@rdf:about]"):
            uri = str(descriptionNode.attrib[curieToTag("rdf:about")])
            yield descriptionNode, uri
        for statementNode in xpath(lxmlNode, "rdf:Statement"):
            uri = str(xpathFirst(statementNode, 'rdf:subject/@rdf:resource'))
            yield statementNode, uri

    def _normalizeRdfDescription(self, descriptionNode):
        descriptionNode = XML(lxmltostringUtf8(descriptionNode).strip())
        cleanup_namespaces(descriptionNode)
        if descriptionNode.tag in CANONICAL_DESCRIPTION_TAGS:
            return descriptionNode
        def _tag2Type(tag):
            return tag.replace('{', '').replace('}', '')
        rdfDescriptionTag = '{%(rdf)s}Description' % namespaces
        if descriptionNode.tag == rdfDescriptionTag:
            return descriptionNode
        descriptionElement = Element(rdfDescriptionTag,
            attrib=descriptionNode.attrib,
            nsmap=descriptionNode.nsmap,
        )
        SubElement(descriptionElement,
            '{%(rdf)s}type' % namespaces,
            attrib={
                '{%(rdf)s}resource' % namespaces: _tag2Type(descriptionNode.tag)
            }
        )
        for childElement in descriptionNode.getchildren():
            descriptionElement.append(deepcopy(childElement))
        return descriptionElement

    def _add(self, recordId, fragments, oaiArgs=None):
        oaiArgs = oaiArgs or {}
        if 'metadataFormats' not in oaiArgs:
            oaiArgs['metadataFormats'] = self._metadataFormats()
        uriUpdates, recordCountUpdates = self._determineUpdates(recordId, fragments)
        for uri, changes in uriUpdates.items():
            uriFragments = self._newFragmentsForUri(uri, changes)
            if len(uriFragments) == 0:
                yield self.all[self._oaiAddRecordLabel].delete(identifier=uri)
                self.call[self._storageLabel].deleteData(identifier=uri, name='rdf')
            else:
                self.call[self._oaiAddRecordLabel].addOaiRecord(identifier=uri, **oaiArgs)
                data = RDF_TEMPLATE % ''.join(fragment.data for fragment in uriFragments.values())
                self.call[self._storageLabel].addData(identifier=uri, name='rdf', data=data)
            yield Yield

        self._registerFragmentsForRecord(recordId, fragments.values())
        for fragmentHash, recordCount in recordCountUpdates.items():
            self._setFragmentRecordCount(fragmentHash, recordCount)

    def _delete(self, recordId, oaiArgs=None):
        yield self._add(recordId, fragments={}, oaiArgs=oaiArgs)

    def _metadataFormats(self):
        return [('rdf', self._rdfxsdUrl, namespaces.rdf)]

    def _determineUpdates(self, recordId, fragments):
        uriUpdates = defaultdict(lambda: defaultdict(list))
        recordCountUpdates = {}

        newFragmentHashes = fragments.keys()
        existingRecordFragments = self._fragmentsForRecord(recordId)
        for fragment in existingRecordFragments:
            if fragment.hash in newFragmentHashes:
                continue
            newCount = recordCountUpdates[fragment.hash] = self._fragmentRecordCount(fragment.hash) - 1
            if newCount == 0:
                uriUpdates[fragment.uri]['remove'].append(fragment.hash)

        existingRecordFragmentHashes = set([fragment.hash for fragment in existingRecordFragments])
        for fragmentHash, fragment in fragments.items():
            if fragmentHash in existingRecordFragmentHashes:
                continue
            newCount = recordCountUpdates[fragmentHash] = self._fragmentRecordCount(fragmentHash) + 1
            if newCount == 1:
                uriUpdates[fragment.uri]['add'].append(fragment)
        return uriUpdates, recordCountUpdates

    def _newFragmentsForUri(self, uri, changes):
        uriFragments = {}
        oaiRecord = self.call.getRecord(identifier=uri)
        if not oaiRecord is None and not oaiRecord.isDeleted:
            data = self.call.getData(identifier=oaiRecord.identifier, name='rdf')
            uriFragments = self._extractFragments(XML(data))
        for fragmentHash in changes['remove']:
            try:
                del uriFragments[fragmentHash]
            except KeyError:
                print >> sys.stderr, 'Warning: hash %s for %s was not found in uriFragments.' % (repr(fragmentHash), repr(uri))
                sys.stderr.flush()
        for fragment in changes['add']:
            uriFragments[fragment.hash] = fragment
        return uriFragments

    def _fragmentsForRecord(self, recordId):
        fragments = []
        encodedFragments = self._fragmentAdmin.get(recordId)
        if encodedFragments:
            # Backwards compatible mode
            if '|' in encodedFragments:
                encodedFragments = fixEncodedFragments(encodedFragments)
                print "Fixing fragments for '{0}'".format(recordId)
                from sys import stdout; stdout.flush()
                self._fragmentAdmin[recordId] = encodedFragments
            # /Backwards compatible mode
            fragments = [
                _Fragment.fromEncodedString(entry) for entry in encodedFragments.split(' ')
            ]
        return fragments

    def _registerFragmentsForRecord(self, recordId, fragments):
        encodedFragments = ' '.join(fragment.asEncodedString() for fragment in fragments)
        if encodedFragments:
            self._fragmentAdmin[recordId] = encodedFragments
        else:
            del self._fragmentAdmin[recordId]

    def _fragmentRecordCount(self, fragmentHash):
        return int(self._fragmentAdmin.get(fragmentHash, 0))

    def _setFragmentRecordCount(self, fragmentHash, count):
        if count == 0:
            del self._fragmentAdmin[fragmentHash]
        else:
            self._fragmentAdmin[fragmentHash] = str(count)


class _Fragment(object):
    def __init__(self, uri, data=None, hash=None):
        self.uri = uri
        self.data = data
        self.hash = hash if hash else self.hashFragment(self.data)

    @staticmethod
    def hashFragment(s):
        return sha1(s).hexdigest()

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ', '.join("%s=%s" % (key, repr(value)) for key, value in self.__dict__.items()))

    def asEncodedString(self):
        return b64encode("{0}|{1}".format(self.hash, self.uri))

    @classmethod
    def fromEncodedString(cls, aString):
        aString = b64decode(aString)
        hash, uri = aString.split('|', 1)
        return cls(uri=uri, hash=hash)


from re import compile
hashRe = compile(r'^[0-9a-f]{40}$')
def fixEncodedFragments(encodedFragments):
    newlist = []
    for fragment in encodedFragments.split(' '):
        if '|' in fragment:
            firstPart = fragment.split('|')[0]
            if hashRe.match(firstPart):
                newlist.append(fragment)
            else:
                newlist[-1] += ' '+fragment
        else:
            try:
                result = b64decode(fragment)
                if '|' in result:
                    newlist.append(result)
                    continue
            except TypeError:
                pass
            newlist[-1] += ' '+fragment

    return ' '.join(b64encode(i) for i in newlist)


def lxmltostringUtf8(lxmlNode, **kwargs):
    return tostring(lxmlNode, encoding="UTF-8", **kwargs)


RDF_TEMPLATE = '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">%s</rdf:RDF>'
CANONICAL_DESCRIPTION_TAGS = set(namespaces.curieToTag(tag) for tag in ['rdf:Description', 'oa:Annotation', 'rdf:Statement'])
