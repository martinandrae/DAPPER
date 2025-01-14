import scipy
import numpy as np
from pathlib import Path
import argparse

iterations = 101000

parser = argparse.ArgumentParser()
parser.add_argument("--number", type=int, default=1, help="Number flag")
args = parser.parse_args()

number = args.number

input_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_HRES_{iterations}_{number}.npy')
output_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_SUBS_{iterations}_{number}.npy')

print("Script started")

def subsample(x):
    x = scipy.signal.decimate(x, 2, n=None, ftype='fir', axis=0)
    x = scipy.signal.decimate(x, 2, n=None, ftype='fir', axis=1)
    return x

def generate_SUBS():
    X_lp = np.load(input_filename)#['sample'].astype('float32')

    if X_lp.shape[1] != (2**7+1)**2:
        print("Input has wrong dimensions")
        return

    X_lp = np.array([X_lp[i].reshape((2**7+1,2**7+1)) for i in range(X_lp.shape[0])])

    X_lp = np.array([subsample(x) for x in X_lp])
    X_lp = X_lp.reshape((X_lp.shape[0], (X_lp.shape[1])*(X_lp.shape[2])))

    np.save(output_filename, X_lp)

generate_SUBS()
print("Script finished")
