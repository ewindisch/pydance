#!/bin/sh

python /usr/lib/python2.2/profile.py pydance.py > /dev/null
mv ~/.pyddr/pydance.log Profile-`date +%s`
