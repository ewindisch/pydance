#!/bin/sh

python /usr/lib/python2.2/profile.py pyddr.py > /dev/null
mv ~/.pyddr/pyddr.log Profile-`date +%s`
