import numpy as np
from pathlib import Path
import scipy
import QG

iterations = 100

sample = QG.gen_complete_run(QG.model_config("sample_generation", {}), iterations)

#local_data_filename = Path(f'/home/sm_maran/dpr_data/samples/LRES_NWP_{iterations}')
#disk_data_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_HRES_{iterations}')

#sample_filename = disk_data_filename
#np.save(sample_filename, sample)

input_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_HRES_{iterations}.npz')
output_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_SUBS_{iterations}.npy')

def subsample(x):
    x = scipy.signal.decimate(x, 2, n=None, ftype='fir', axis=0)
    x = scipy.signal.decimate(x, 2, n=None, ftype='fir', axis=1)
    return x

def generate_SUBS():
    print(sample.shape)
    X_lp = sample#np.load(input_filename)['sample'].astype('float32')

    if X_lp.shape[1] != (2**7+1)**2:
        print("Input has wrong dimensions")
        return

    X_lp = np.array([X_lp[i].reshape((2**7+1,2**7+1)) for i in range(X_lp.shape[0])])

    X_lp = np.array([subsample(x) for x in X_lp])
    X_lp = X_lp.reshape((X_lp.shape[0], (X_lp.shape[1])*(X_lp.shape[2])))

    np.save(output_filename, X_lp)

generate_SUBS()
