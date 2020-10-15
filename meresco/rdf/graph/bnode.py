## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2011-2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

from .abstract import Identifier


class BNode(Identifier):
    nextGenId = 0

    def __init__(self, value=None):
        # if not isinstance(value, basestring):
        #     raise ValueError('Expected a stringlike object')
        if value is None:
            self.value = "_:id" + str(BNode.nextGenId)
            BNode.nextGenId += 1
        else:
            self.value = str(value) if value else value

    def isBNode(self):
        return True

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.value))

    def __eq__(self, other):
        return other.__class__ is self.__class__ and (other.value == self.value)

    def __cmp__(self, other):
        return cmp(self.value, other.value)

