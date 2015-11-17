## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from lxml.etree import Element, SubElement
from meresco.xml import namespaces
from meresco.xml.namespaces import curieToTag

def makeAnnotationEnvelope(uri, targetUri, motiveUri, annotatedByUri):
    rdfElement = Element(
        RDF_RDF_TAG,
        nsmap=NSMAP_RDF,
    )
    annotationElement = SubElement(
        rdfElement,
        OA_ANNOTATION_TAG,
        attrib={RDF_ABOUT_TAG: unicode(uri)},
        nsmap=NSMAP_OA,
    )
    SubElement(
        annotationElement,
        OA_ANNOTATED_BY_TAG,
        attrib={RDF_RESOURCE_TAG: unicode(annotatedByUri)}
    )
    SubElement(
        annotationElement,
        OA_MOTIVATED_BY_TAG,
        attrib={RDF_RESOURCE_TAG: unicode(motiveUri)}
    )
    SubElement(
        annotationElement,
        OA_HAS_TARGET_TAG,
        attrib={RDF_RESOURCE_TAG: unicode(targetUri)}
    )
    hasBodyElement = SubElement(
        annotationElement,
        OA_HAS_BODY_TAG
    )
    return rdfElement, hasBodyElement

def buildBodyDescription(hasBodyElement, elements):
    prefixes = determinePrefixes(elements)
    bodyDescriptionElement = SubElement(
        hasBodyElement,
        namespaces.curieToTag('rdf:Description'),
        nsmap=dict((prefix, namespaces[prefix]) for prefix in prefixes))
    bodyDescriptionElement.extend(elements)

def determinePrefixes(elements):
    prefixes = set()
    for element in elements:
        prefixes.add(_getPrefix(element))
        for desc in element.iterdescendants():
            prefixes.add(_getPrefix(desc))
    return prefixes

def _getPrefix(element):
    prefix, _ = namespaces.tagToCurie(element.tag).split(':', 1)
    return prefix

OA_ANNOTATED_BY_TAG = curieToTag('oa:annotatedBy')
OA_ANNOTATION_TAG = curieToTag('oa:Annotation')
OA_HAS_BODY_TAG = curieToTag('oa:hasBody')
OA_HAS_TARGET_TAG = curieToTag('oa:hasTarget')
OA_MOTIVATED_BY_TAG = curieToTag('oa:motivatedBy')
RDF_ABOUT_TAG = curieToTag('rdf:about')
RDF_RDF_TAG = curieToTag('rdf:RDF')
RDF_RESOURCE_TAG = curieToTag('rdf:resource')
NSMAP_RDF = namespaces.select('rdf')
NSMAP_OA = namespaces.select('oa')