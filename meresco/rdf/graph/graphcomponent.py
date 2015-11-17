## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2013-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2013-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
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

from os import walk
from os.path import join, basename, isfile

from lxml.etree import XML

from weightless.core import compose
from meresco.core import Observable

from .graph import Graph
from .rdfparser import RDFParser


class GraphComponent(Observable):
    def __init__(self, rdfSources, name=None):
        Observable.__init__(self, name=name)
        self._graph = Graph()
        for context, contentType, data in iterRdfSources(rdfSources):
            lxmlNode = XML(data)
            RDFParser(sink=self._graph).parse(lxmlNode)

    def makeGraph(self, lxmlNode=None):
        graph = Graph()
        parser = RDFParser(sink=graph)
        parser.parse(lxmlNode=lxmlNode)
        return graph

    def __getattr__(self, attr):
        return getattr(self._graph, attr)


def iterRdfSources(rdfSources):
    for rdfSource in rdfSources:
        if hasattr(rdfSource, 'asRdfXml'):
            yield rdfSource.context, 'text/xml', ''.join(compose(rdfSource.asRdfXml()))
        elif isfile(rdfSource):
            yield basename(rdfSource), contentType(rdfSource), open(rdfSource).read()
        else:
            for context, rdfFilePath in iterRdfDataFiles(rdfSource):
                yield context, contentType(rdfFilePath), open(rdfFilePath).read()

def contentType(filename):
    if filename.endswith('.rdf'):
        return 'text/xml'
    elif filename.endswith('.nt'):
        return 'text/plain'
    else:
        raise ValueError("Unknown file format")

def iterRdfDataFiles(rdfDir):
    for (dirPath, _, fns) in walk(rdfDir):
        for fn in fns:
            path = join(dirPath, fn)
            yield 'file:%s' % basename(path), path
