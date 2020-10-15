## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2011-2013, 2015, 2020 Seecr (Seek You Too B.V.) https://seecr.nl
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

import rfc3987

class Uri(object):
    def __init__(self, value):
        if not isinstance(value, str):
            raise ValueError('Expected a stringlike object')
        self.value = value

    @classmethod
    def fromDict(cls, valueDict):
        return cls(valueDict['value'])

    def __str__(self):
        return self.value

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, repr(self.value))

    def __eq__(self, other):
        return other.__class__ is self.__class__ and other.value == self.value

    @staticmethod
    def matchesUriSyntax(value):
        try:
            rfc3987.parse(value, rule='IRI')
            return True
        except ValueError:
            return False

