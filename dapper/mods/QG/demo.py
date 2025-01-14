"""Demonstrate the QG (quasi-geostrophic) model."""

import numpy as np
import scipy.ndimage.filters as filters
from matplotlib import pyplot as plt

from dapper.mods.QG import default_prms, nx, sample_filename, square
from dapper.tools.progressbar import progbar

from pathlib import Path

def show(x0, psi=True, ax=None):
    # Whether to show psi (streamfun) or q (potential vorticity)
    def psi_or_q(x):
        return x if psi else compute_q(x)
    # Create fig if necessary
    if ax == None:
        fig, ax = plt.subplots()
    # Init ax
    im = ax.imshow(psi_or_q(square(x0)))
    if psi:
        im.set_clim(-30, 30)
    else:
        im.set_clim(-28e4, 25e4)

    # Define plot update fun, which we return
    def update(x):
        im.set_data(psi_or_q(square(x)))
    return update


# Although psi is the state variable, q looks cooler.
# q = Nabla^2(psi) - F*psi.
dx = 1/(nx-1)


def compute_q(psi):
    Lapl = filters.laplace(psi, mode='constant')/dx**2
    # mode='constant' coz BCs are: psi = nabla psi = nabla^2 psi = 0
    return Lapl - default_prms['F']*psi


nwp_data_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/LRES_NWP_10000.npy')
data_filename = Path(f'/nobackup/smhid20/users/sm_maran/dpr_data/simulations/LRES_10000.npy')

if __name__ == "__main__":
    fig, (ax1, ax2) = plt.subplots(ncols=2, sharex=True, sharey=True, figsize=(8, 4))
    for ax in (ax1, ax2):
        ax.set_aspect('equal', 'box')
    ax1.set_title(r'$\psi$')
    ax2.set_title('$q$')

    #xx = np.load(sample_filename)['sample']
    X_hres = np.load(data_filename)
    X_lres = np.load(nwp_data_filename)
    setter1 = show(X_hres[0], psi=True , ax=ax1)
    setter2 = show(X_lres[0], psi=True , ax=ax2)
    #setter2 = show(xx[0], psi=False, ax=ax2)

    #for k, i in progbar(list(xx), "Animating"):
    for k in range(X_hres.shape[0]):
        x1 = X_hres[k]
        x2 = X_lres[k]
        if k % 2 == 0:
            fig.suptitle("k: "+str(k))
            setter1(x1)
            setter2(x2)
            plt.pause(0.01)
