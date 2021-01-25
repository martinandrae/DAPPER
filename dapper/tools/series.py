"""Time series management and processing."""

from dataclasses import dataclass

import numpy as np
from numpy import nan

import dapper.tools.utils as utils
from dapper.dict_tools import NicePrint
from dapper.dpr_config import rc
from dapper.tools.math import center, is1d, log10int, round2, round2sigfig


def auto_cov(xx, nlags=4, zero_mean=False, corr=False):
    """
    Auto covariance function, computed along axis 0.

    - `nlags`: max lag (offset) for which to compute acf.
    - `corr` : normalize acf by `acf[0]` so as to return auto-CORRELATION.

    With `corr=True`, this is identical to
    `statsmodels.tsa.stattools.acf(xx,True,nlags)`
    """
    assert nlags < len(xx)

    N = len(xx)
    A = xx if zero_mean else center(xx)[0]
    acovf = np.zeros((nlags+1,)+xx.shape[1:])

    for i in range(nlags+1):
        Left  = A[np.arange(N-i)]
        Right = A[np.arange(i, N)]
        acovf[i] = (Left*Right).sum(0)/(N-i)

    if corr:
        acovf /= acovf[0]

    return acovf


def fit_acf_by_AR1(acf_empir, nlags=None):
    """Fit an empirical auto cov function (ACF) by that of an AR1 process.

    - `acf_empir`: auto-corr/cov-function.
    - `nlags`: length of ACF to use in AR(1) fitting
    """
    if nlags is None:
        nlags = len(acf_empir)

    # geometric_mean = ss.mstats.gmean
    def geometric_mean(xx): return np.exp(np.mean(np.log(xx)))

    def mean_ratio(xx):
        return geometric_mean([xx[i]/xx[i-1] for i in range(1, len(xx))])

    # Negative correlation => Truncate ACF
    neg_ind   = utils.find_1st_ind(np.array(acf_empir) <= 0)
    acf_empir = acf_empir[:neg_ind]

    if len(acf_empir) == 0:
        return 0
    elif len(acf_empir) == 1:
        return 0.01
    else:
        return mean_ratio(acf_empir)


def estimate_corr_length(xx):
    """
    For explanation, see `dapper.mods.LA.homogeneous_1D_cov`.
    Also note that, for exponential corr function, as assumed here,

    $$\\text{corr}(L) = \\exp(-1) \\approx 0.368$$
    """
    assert is1d(xx)
    acovf = auto_cov(xx, min(100, len(xx)-2))
    a     = fit_acf_by_AR1(acovf)
    if a == 0:
        L = 0
    else:
        L = 1/np.log(1/a)
    return L

@dataclass
class UncertainQtty():
    """Data container associating uncertainty (confidence) to a quantity.

    Includes intelligent rounding and printing functionality.

    Examples:
    >>> for c in [.01, .1, .2, .9, 1]:
    ...    print(UncertainQtty(1.2345, c))
    1.23 ±0.01
    1.2 ±0.1
    1.2 ±0.2
    1.2 ±0.9
    1 ±1

    >>> for c in [.01, 1e-10, 1e-17, 0]:
    ...    print(UncertainQtty(1.2, c))
    1.20 ±0.01
    1.2000000000 ±1e-10
    1.19999999999999996 ±1e-17
    1.2000000000 ±0

    Note that in the case of a confidence of exactly 0,
    it defaults to 10 decimal places.
    Meanwhile, a NaN confidence yields printing using `rc.sigfig`:

    >>> print(UncertainQtty(1.234567, np.nan))
    1.235 ±nan

    Also note the effect of large uncertainty:

    >>> for c in [1, 9, 10, 11, 20, 100, np.inf]:
    ...    print(UncertainQtty(12, c))
    12 ±1
    12 ±9
    10 ±10
    10 ±10
    10 ±20
    0 ±100
    0 ±inf
    """

    val: float
    conf: float

    def round(self, mult=1.0):  # noqa
        """Round intelligently.

        - `conf` to 1 sig. fig.
        - `val`:
            - to precision: `mult*conf`
            - fallback: `rc.sigfig`
        """
        if np.isnan(self.conf):
            # Fallback to rc.sigfig
            c = self.conf
            v = round2sigfig(self.val, rc.sigfig)
        else:
            # Normal/general case
            c = round2sigfig(self.conf, 1)
            v = round2(self.val, mult*self.conf)
        return v, c

    def __str__(self):
        """Returns 'val ±conf'.

        The value string contains the number of decimals required by the confidence.

        Note: the special cases require processing on top of `round`.
        """
        v, c = self.round()
        if np.isnan(c):
            # Rounding to fallback (rc.sigfig) already took place
            return f"{v} ±{c}"
        if c == 0:
            # 0 (i.e. not 1e-300) never arises "naturally" => Treat it "magically"
            # by truncating to a default. Also see https://stackoverflow.com/a/25899600
            n = -10
        else:
            # Normal/general case.
            n = log10int(c)
        # Ensure we get 1.30 ±0.01, NOT 1.3 ±0.01:
        frmt = "%.f"
        if n < 0:
            frmt = "%%0.%df" % -n
        v = frmt % v
        return f"{v} ±{c}"

    def __repr__(self):
        """Essentially the same as `__str__`."""
        v, c = str(self).split(" ±")
        return self.__class__.__name__ + f"(val={v}, conf={c})"

def mean_with_conf(xx):
    """Compute the mean of a 1d iterable ``xx``.

    Also provide confidence of mean,
    as estimated from its correlation-corrected variance.
    """
    mu = np.mean(xx)
    N  = len(xx)
    # TODO 3: review
    if (not np.isfinite(mu)) or N <= 5:
        uq = UncertainQtty(mu, np.nan)
    elif np.allclose(xx, mu):
        uq = UncertainQtty(mu, 0)
    else:
        acovf = auto_cov(xx)
        var   = acovf[0]
        var  /= N
        # Estimate (fit) ACF
        a = fit_acf_by_AR1(acovf)
        # If xx[k] where independent of xx[k-1],
        # then std_of_mu is the end of the story.
        # The following corrects for the correlation in the time series.
        #
        # See https://stats.stackexchange.com/q/90062
        # c = sum([(N-k)*a**k for k in range(1,N)])
        # But this series is analytically tractable:
        c = ((N-1)*a - N*a**2 + a**(N+1)) / (1-a)**2
        confidence_correction = 1 + 2/N * c
        var *= confidence_correction
        uq = UncertainQtty(mu, np.sqrt(var))
    return uq


class StatPrint(NicePrint):
    """Set NicePrint options suitable for stats."""
    printopts = dict(
        excluded=NicePrint.printopts["excluded"]+["HMM", "LP_instance"],
        ordering="linenumber",
        reverse=True,
        indent=2,
        aliases={
            'f': 'Forecast  (.f)',
            'a': 'Analysis  (.a)',
            's': 'Smoothed  (.s)',
            'u': 'Universal (.u)',
            'm': 'Field mean (.m)',
            'ma': 'Field mean-abs (.ma)',
            'rms': 'Field root-mean-square (.rms)',
            'gm': 'Field geometric-mean (.gm)'
        },
    )

    # Adjust np.printoptions before NicePrint
    def __repr__(self):
        with np.printoptions(threshold=10, precision=3):
            return super().__repr__()

    def __str__(self):
        with np.printoptions(threshold=10, precision=3):
            return super().__str__()


@utils.monitor_setitem
class DataSeries(StatPrint):
    """Basically just an ``np.ndarray``. But adds:

    - Possibility of adding attributes.
    - The class (type) provides way to acertain if an attribute is a series.

    Note: subclassing ``ndarray`` is too dirty => We'll just use the
    ``array`` attribute, and provide ``{s,g}etitem``."""

    def __init__(self, shape, **kwargs):
        self.array = np.full(shape, nan, **kwargs)

    def __len__(self): return len(self.array)
    def __getitem__(self, key): return self.array[key]
    def __setitem__(self, key, val): self.array[key] = val


@utils.monitor_setitem
class FAUSt(DataSeries, StatPrint):
    """Container for time series of a statistic from filtering.

    Four attributes, each of which is an ndarray:

    - .f for forecast      , (KObs+1,)+item_shape
    - .a for analysis      , (KObs+1,)+item_shape
    - .s for smoothed      , (KObs+1,)+item_shape
    - .u for universial/all, (K   +1,)+item_shape

    If store_u=False, then .u series has shape (1,)+item_shape,
    wherein only the most-recently-written item is stored.

    Series can also be indexed as in

        self[kObs,'a']
        self[whatever,kObs,'a']
        # ... and likewise for 'f' and 's'. For 'u', can use:
        self[k,'u']
        self[k,whatever,'u']

    .. note:: If a data series only pertains to the analysis,
              then you should use a plain np.array instead.
    """

    def __init__(self, K, KObs, item_shape, store_u, store_s, **kwargs):
        """Constructor.

         - item_shape : shape of an item in the series.
         - store_u    : if False: only the current value is stored.
         - kwargs     : passed on to ndarrays.
        """

        self.f     = np.full((KObs+1,)+item_shape, nan, **kwargs)
        self.a     = np.full((KObs+1,)+item_shape, nan, **kwargs)
        if store_s:
            self.s = np.full((KObs+1,)+item_shape, nan, **kwargs)
        if store_u:
            self.u = np.full((K   + 1,)+item_shape, nan, **kwargs)
        else:
            self.u = np.full((1,)+item_shape, nan, **kwargs)

    # We could just store the input values for these attrs, but using
    # property => Won't be listed in vars(self), and un-writeable.
    item_shape = property(lambda self: self.a.shape[1:])
    store_u    = property(lambda self: len(self.u) > 1)

    def _ind(self, key):
        "Aux function to unpack ``key`` (k,kObs,faus)"
        if key[-1] == 'u':
            return key[0] if self.store_u else 0
        else:
            return key[-2]

    def __setitem__(self, key, item):  getattr(self, key[-1])[self._ind(key)] = item
    def __getitem__(self, key): return getattr(self, key[-1])[self._ind(key)]


class RollingArray:
    """ND-Array that implements "leftward rolling" along axis 0.

    Used for data that gets plotted in sliding graphs."""

    def __init__(self, shape, fillval=nan):
        self.array = np.full(shape, fillval)
        self.k1 = 0      # previous k
        self.nFilled = 0

    def insert(self, k, val):
        dk = k-self.k1

        # Old (more readable?) version:
        # if dk in [0,1]: # case: forecast or analysis update
        # self.array = np.roll(self.array, -1, axis=0)
        # elif dk>1:      # case: user has skipped ahead (w/o liveplotting)
        # self.array = np.roll(self.array, -dk, axis=0)
        # self.array[-dk:] = nan
        # self.array[-1] = val

        dk = max(1, dk)
        # TODO 7: Should have used deque?
        self.array = np.roll(self.array, -dk, axis=0)
        self.array[-dk:] = nan
        self.array[-1:] = val

        self.k1 = k
        self.nFilled = min(len(self), self.nFilled+dk)

    def leftmost(self):
        return self[len(self)-self.nFilled]

    def span(self):
        return (self.leftmost(),  self[-1])

    @property
    def T(self):
        return self.array.T

    def __array__(self, dtype=None): return self.array
    def __len__(self): return len(self.array)
    def __repr__(self): return 'RollingArray:\n%s' % str(self.array)
    def __getitem__(self, key): return self.array[key]

    def __setitem__(self, key, val):
        # Don't implement __setitem__ coz leftmost() is then
        # not generally meaningful (i.e. if an element is set in the middle).
        # Of course self.array can still be messed with.
        raise AttributeError("Values should be set with update()")
