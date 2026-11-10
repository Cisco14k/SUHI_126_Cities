"""Heat cost of sealing under projected climates to 2100 (screening only). The causal transfer model, fitted on
all city-regions, is evaluated with each city's CMIP6 delta-changed climate descriptors (five GCMs, SSP2-4.5 and
SSP5-8.5, 2041-2070 and 2071-2100) and its present surface, for its fringe cells (1-km impervious cover 10-50%).
Uncertainty: GCM spread and a city bootstrap of the transfer model (200 resamples). Descriptor values outside the
range of the 126 present-day climates are flagged as extrapolation."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import transfer as T
I = T.build(); H, Rz, clim = I['H'], I['R'], I['clim']
D = pd.read_csv(f'{RES}/cmip6_deltas.csv')
rng = np.random.default_rng(3); cs = np.array(sorted(Rz.city.unique()))
fits = [T.Causal().fit(Rz)]
for b in range(200):
    bs = rng.choice(cs, len(cs), replace=True)
    Rb = pd.concat([Rz[Rz.city == c].assign(city=f'{c}#{i}') for i, c in enumerate(bs)], ignore_index=True)
    fits.append(T.Causal().fit(Rb, lams=(fits[0].lam,)))
class CausalClim(T.Causal):
    COLS = ['isa_cell', 'log_aridity', 'tmax_warm', 'vpd_warm', 'log_soil', 'ws']
    def fit(self, R, lams=(0.1, 1, 10, 100, 1000)):
        V = T.vmat(R, R.wc_tree.values, R.wc_built.values)[self.COLS]; self.mu, self.sd = V.mean(), V.std() + 1e-9
        Z = np.column_stack([np.ones(len(R)), ((V - self.mu) / self.sd).values]) * R.Dt.values[:, None]
        self.lam = 1.0; self.beta = self._ridge(Z, R.Yt.values, 1.0); return self
    def tau(self, V):
        V = V[self.COLS]; return self.beta[0] + ((V - self.mu) / self.sd).values @ self.beta[1:]
alt = CausalClim().fit(Rz)
rng_lo = clim[T.CLIM].min(); rng_hi = clim[T.CLIM].max()
rows = []
for c in cs:
    h = H[(H.city == c)]; f = h[(h.nb1k_isa >= 0.1) & (h.nb1k_isa < 0.5)]
    if len(f) < 100: f = h
    f = f.sample(min(len(f), 2000), random_state=0)
    def tau(cl, fit):
        g = f.copy()
        for v in T.CLIM: g[v] = cl[v]
        return float(np.mean(fit.tau(T.vmat(g, g.wc_tree.values, g.wc_built.values))))
    base = {v: clim.loc[c, v] for v in T.CLIM}
    t0 = np.array([tau(base, ft) for ft in fits]); a0 = tau(base, alt)
    rows.append(dict(city=c, model='present', scen='present', period='1991-2020', tau=t0[0], tau_lo=np.quantile(t0[1:], 0.05), tau_hi=np.quantile(t0[1:], 0.95), extrap=0, tau_alt=a0))
    for _, r in D[D.city == c].iterrows():
        cl = dict(aridity=r.aridity_f, tmax_warm=r.tmax_warm_f, vpd_warm=r.vpd_warm_f, soil=r.soil_f, ws=r.ws_f)
        tb = np.array([tau(cl, ft) for ft in fits[:51]])
        ex = int(sum((cl[v] < rng_lo[v]) or (cl[v] > rng_hi[v]) for v in T.CLIM))
        rows.append(dict(city=c, model=r.model, scen=r.scen, period=r.period, tau=tb[0], tau_lo=np.quantile(tb[1:], 0.05), tau_hi=np.quantile(tb[1:], 0.95),
                         d_tau=tb[0] - t0[0], d_tau_lo=np.quantile(tb[1:] - t0[1:51], 0.05), d_tau_hi=np.quantile(tb[1:] - t0[1:51], 0.95),
                         dtmax_warm=r.dtmax_warm, rppt=r.rppt, extrap=ex, tau_alt=tau(cl, alt), d_tau_alt=tau(cl, alt) - a0))
P = pd.DataFrame(rows).merge(clim[['zone', 'region']], left_on='city', right_index=True)
P.to_csv(f'{RES}/projection.csv', index=False)
print(P[P.scen != 'present'].groupby(['scen', 'period']).agg(d_tau=('d_tau', 'median'), dT=('dtmax_warm', 'median'), extrap=('extrap', lambda x: (x > 0).mean())))
print(P[P.scen != 'present'].groupby(['scen', 'period']).d_tau_alt.median()); print('alt coef', np.round(alt.beta, 3))
print('coef', dict(zip(['int'] + T.VMOD, np.round(fits[0].beta, 3))), 'lam', fits[0].lam)
