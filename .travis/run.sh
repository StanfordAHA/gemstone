#!/bin/bash

# BEGIN GENESIS2 INSTALL
git clone https://github.com/StanfordVLSI/Genesis2.git
rm -rf Genesis2/Genesis2Tools/PerlLibs/ExtrasForOldPerlDistributions/Compress
export GENESIS_HOME=`pwd`/Genesis2/Genesis2Tools
export PATH=$GENESIS_HOME/bin:$GENESIS_HOME/gui/bin:$PATH
export PERL5LIB=$GENESIS_HOME/PerlLibs/ExtrasForOldPerlDistributions:$PERL5LIB
# END GENESIS2 INSTALL

# force color
export PYTEST_ADDOPTS="--color=yes"

cd /gemstone/

pytest --codestyle gemstone \
       --cov gemstone       \
       -v --cov-report term-missing tests
