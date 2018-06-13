from ESL import ESL, ms2tick
from time import sleep

F =	(1, 2, 3) # KHz
A =	1023
w =	0.1 # ms
T1 =	500 # ms
T2 =	500 # ms

esl = ESL()

for f in F:
	esl.stop()
	esl.trig_dis()

	t = T1 + T2
	t1 = 1. / f
	n = T1 / t1

	if t1 <= w:
		raise NameError, "ERROR: 1/f <= w"

	esl.set_params(t = t * ms2tick, n = n, t1 = t1 * ms2tick, w = w * ms2tick, a = A)

	for i in xrange(5):
		esl.stop()
		esl.single()
		sleep(1)

	esl.trig_en()
	sleep(50)

	esl.stop()
	esl.trig_dis()
	sleep(5)
