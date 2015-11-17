## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2014-2015 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015 Drents Archief http://www.drentsarchief.nl
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


class _GraphElement(object):
    """
    Common superclass of all RDF-Graph nodes (Uri(Ref), BNode and Literal);
    signifies resource is valid anywhere in a RDF-Graph.
    """

    def isUri(self):
        return False

    def isBNode(self):
        return False

    def isLiteral(self):
        return False

    def isIdentifier(self):
        return False


class Identifier(_GraphElement):
    """
    Superclass of Uri(Ref) and BNode; signifies resource is valid as a (possible) branch in a RDF-Graph.
    """

    def isIdentifier(self):
        return True


def isGraphElement(o):
    return isinstance(o, _GraphElement)

