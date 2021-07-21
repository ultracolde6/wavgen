import h5py
import matplotlib.pyplot as plt
import numpy as np


filename = '../tests/sweep_1-10_1-1-1.h5'

with h5py.File(filename, "r") as f:
    print("Keys: %s" % f.keys())
    key = list(f.keys())[0]

    dataA = list(f[key])
print('done')
with h5py.File(filename, "r") as f:
    print("Keys: %s" % f.keys())
    key = list(f.keys())[1]

    dataB = list(f[key])


with h5py.File(filename, "r") as f:
    print("Keys: %s" % f.keys())
    key = list(f.keys())[2]

    dataAB = list(f[key])


plt.plot(dataB)
plt.show()