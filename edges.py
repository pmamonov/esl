from numpy import loadtxt, zeros

def load(fn):
	tv = loadtxt(fn)
	
	for i in xrange(tv.shape[0]):
		if tv[i,1] == 0:
			tv = tv[i:]
			break
	return tv

def edges(tv):
	posed = tv[1:,1] - tv[:-1,1] == 1
	neged = tv[1:,1] - tv[:-1,1] == -1
	tposed = tv[1:,0][posed]
	tneged = tv[1:,0][neged]
	return tposed, tneged

def pulse_stat(fn):
	tv = load(fn)
	tposed, tneged = edges(tv)
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

def waveform(fn):
	tv = load(fn)
	tposed, tneged = edges(tv)
	n = min(tposed.shape[0], tneged.shape[0])
	t = zeros(4 * n)
	v = zeros(4 * n)
	for i in xrange(n):
		j = 4 * i
		t[j] = tposed[i]
		v[j] = 0
		t[j + 1] = tposed[i]
		v[j + 1] = 1
		t[j + 2] = tneged[i]
		v[j + 2] = 1
		t[j + 3] = tneged[i]
		v[j + 3] = 0
	return t, v

if __name__ == "__main__":
	import sys
	fn = sys.argv[1]
	pulse_stat(fn)
