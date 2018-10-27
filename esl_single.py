#!/usr/bin/python

#
# This is API usage example script for running stimulation.
# ------------------------------------------------------------------
# Part of "Firmware/API/GUI for x-SLON" project.
# http://github.com/pmamonov/esl
#

import sys
from time import sleep
from ESL import ESL, ms2tick

if len(sys.argv) < 2:
	print """
USAGE: %s NUMBER
	NUMBER - pulse duration in seconds, e.g. 4.2.
""" % sys.argv[0]
	exit(1)

# parse user-supplied number of seconds
delay = float(sys.argv[1])
# find the device
esl = ESL()
# setup stimulation parameters
t = 100
p = {
	't':	t * ms2tick,
	'n':	1,
	't1':	t * ms2tick,
	'w':	t * ms2tick,
	'a':	1,
}
# apply stimulation parameters
esl.set_params(**p)
# start stimulation
esl.start()
# wait for user-supplied number of seconds
sleep(delay)
# stop stimulation
esl.stop()
