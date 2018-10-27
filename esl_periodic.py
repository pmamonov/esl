#!/usr/bin/python

#
# This is API usage example script for running stimulation.
# ------------------------------------------------------------------
# Part of "Firmware/API/GUI for x-SLON" project.
# http://github.com/pmamonov/esl
#

import sys
from time import sleep, time
from ESL import ESL, ms2tick

period = 1. # s
length = 10 # ms

p = {
	't':	length * ms2tick,
	'n':	1,
	't1':	length * ms2tick,
	'w':	length * ms2tick,
	'a':	1,
}

# find the device
esl = ESL()
# apply stimulation parameters
esl.set_params(**p)

t = time() + period
while True:
	print >> sys.stdout, time()
	sys.stdout.flush()
	esl.single()
	while (time() < t):
		sleep(.01)
	t += period
