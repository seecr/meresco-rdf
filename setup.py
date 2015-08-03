#!/usr/bin/env python
# -*- coding: utf-8 -*-
## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

from distutils.core import setup
from os import walk

packages = []
for path, dirs, files in walk('meresco'):
    if '__init__.py' in files and path != 'meresco':
        packages.append(path.replace('/', '.'))

setup(
    name = 'meresco-rdf',
    packages = [
        'meresco',                          #DO_NOT_DISTRIBUTE
    ] + packages,
    version = '%VERSION%',
    url = 'http://seecr.nl',
    author = 'Seecr (Seek You Too B.V.)',
    author_email = 'info@seecr.nl',
    description = 'Meresco RDF contains components to handle RDF data.',
    long_description = 'Meresco RDF contains components to handle RDF data.',
    license = 'GPL',
    platforms = 'all',
)
