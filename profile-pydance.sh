#!/bin/sh

python /usr/lib/python2.2/profile.py pydance.py > /dev/null
mv ~/.pydance/pydance.log Profile-`date +%s`
