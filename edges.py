from numpy import loadtxt

def pulse_stat(fn):
	tv = loadtxt(fn)
	
	for i in xrange(tv.shape[0]):
		if tv[i,1] == 0:
			tv = tv[i:]
			break

	posed = tv[1:,1] - tv[:-1,1] == 1
	neged = tv[1:,1] - tv[:-1,1] == -1
	tposed = tv[1:,0][posed]
	tneged = tv[1:,0][neged]
	w = tneged - tposed
	dtposed = tposed[1:] - tposed[:-1]

	print "pulse count: %d" % tposed.shape[0]
	m = dtposed.mean()
	print "period: %.6f %.6f +%.6f %.6f" % (m,
				    dtposed.min() - m,
				    dtposed.max() - m,
				    dtposed.std())
	m = w.mean()
	print "width: %.6f %.6f +%6f %.6f" % (m,
					w.min() - m,
					w.max() - m,
					w.std())
	return dtposed, w

if __name__ == "__main__":
	import sys
	fn = sys.argv[1]
	pulse_stat(fn)
