#!/bin/bash
## begin license ##
#
# Meresco RDF contains components to handle RDF data.
#
# Copyright (C) 2012-2013, 2015 Seecr (Seek You Too B.V.) http://seecr.nl
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

set -e
mydir=$(cd $(dirname $0);pwd)

source /usr/share/seecr-tools/functions.d/test

rm -rf tmp build

definePythonVars

$PYTHON setup.py install --root tmp
cp -r test tmp/test

removeDoNotDistribute tmp
find tmp -type f -exec sed -e \
    "s,usrSharePath = .*,usrSharePath = '$mydir/tmp/usr/share/meresco-rdf',;
    s,documentationPath = .*,documentationPath = '$mydir/tmp/usr/share/doc/meresco-rdf',;
    s,binDir = '/usr/bin',binDir = '$mydir/tmp/usr/bin',;
    " -i {} \;

if [ -z "$@" ]; then
    runtests "alltests.sh"
else
    runtests "$@"
fi

rm -rf tmp build

