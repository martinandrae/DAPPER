import numpy as np
from pathlib import Path
import QG
import argparse

spinup=1000
old_iterations = 101000
iterations = old_iterations-spinup

parser = argparse.ArgumentParser()
parser.add_argument("--number", type=int, default=1, help="Number flag")
args = parser.parse_args()

number = args.number

# Rest of your code...

disk_new_data_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_HRES_{old_iterations}_{number}')
disk_old_data_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_HRES_{old_iterations}_{number-1}.npy')

X_lp = np.load(disk_old_data_filename)

X_lp = X_lp[-1,:]

model = QG.model_config("MY_step_model", {})
simulator = QG.modelling.with_recursion(model.step, prog=False)

sample = simulator(X_lp, iterations, 0.0, model.prms["dtout"])

np.save(disk_new_data_filename, sample)
