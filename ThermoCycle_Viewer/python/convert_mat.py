import DyMat, h5py, numpy as np
d = DyMat.DyMatFile('../sample_results.mat')

h = h5py.File('results_out.h5','w')

for var in d.names():
    h.create_dataset(var, data = d.data(var))
    
t = np.array(list(d.abscissa(2, valuesOnly = True)),dtype='double')

h.create_dataset('time', data = t)

h.close()