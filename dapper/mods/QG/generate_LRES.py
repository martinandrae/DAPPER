import numpy as np
from pathlib import Path

from dapper.mods import QG

iterations = 101000
n = 90000
kmax = 150

input_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_SUBS_{iterations}.npy')
output_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/QG_samples_LRES_{iterations}_n_{n}_k_{kmax}.npy')

X_lp = np.load(input_filename)

model = QG.model_config("MY_step_model", {})
simulator = QG.modelling.with_recursion(model.step, prog=False)

N = X_lp.shape[0]
prd_x = slice(n, N)

sample = simulator(X_lp[prd_x], kmax, 0.0, model.prms["dtout"])

np.save(output_filename, sample)
