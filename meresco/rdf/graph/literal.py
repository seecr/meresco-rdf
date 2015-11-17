## begin license ##
#
# "NBC+" also known as "ZP (ZoekPlatform)" is
#  a project of the Koninklijke Bibliotheek
#  and provides a search service for all public
#  libraries in the Netherlands.
#
# Copyright (C) 2011-2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from .abstract import _GraphElement


class Literal(_GraphElement):
    def __init__(self, value, lang=None):
        # if not isinstance(value, basestring):
        #     raise ValueError('Expected a stringlike object')
        self.value = unicode(value) if value else value
        self.lang = unicode(lang) if lang is not None else None
        # datatype  (still missing)

    def isLiteral(self):
        return True

    def __eq__(self, other):
        return other.__class__ is self.__class__ and self.value == other.value and other.lang == self.lang

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __str__(self):
        if self.lang:
            return "%s@%s" % (repr(self.value), self.lang)
        return self.value

    def __repr__(self):
        template = "%%s(%%s%s)"
        template = template % (", lang=" + repr(self.lang) if self.lang else "")
        return template % (self.__class__.__name__, repr(self.value))

    def __cmp__(self, other):
        return cmp(self.value, other.value)
