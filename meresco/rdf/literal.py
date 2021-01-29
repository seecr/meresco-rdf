## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2011-2013, 2015, 2020-2021 Seecr (Seek You Too B.V.) https://seecr.nl
# Copyright (C) 2015, 2020-2021 Stichting Kennisnet https://www.kennisnet.nl
# Copyright (C) 2020-2021 Data Archiving and Network Services https://dans.knaw.nl
# Copyright (C) 2020-2021 SURF https://www.surf.nl
# Copyright (C) 2020-2021 The Netherlands Institute for Sound and Vision https://beeldengeluid.nl
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


class Literal(object):
    def __init__(self, value, lang=None):
        if not isinstance(value, str):
            raise ValueError('Expected a stringlike object')
        self.value = value
        self.lang = lang

    @classmethod
    def fromDict(cls, valueDict):
        return cls(
            value=valueDict['value'],
            lang=valueDict.get('xml:lang', None))

    def __eq__(self, other):
        return other.__class__ is self.__class__ and self.value == other.value and other.lang == self.lang

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        if self.lang:
            return "%s@%s" % (repr(self.value), self.lang)
        return self.value

    def __repr__(self):
        template = "%%s(%%s%s)"
        template = template % (", lang=" + repr(self.lang) if self.lang else "")
        return template % (self.__class__.__name__, repr(self.value))
