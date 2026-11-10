"""Repeated simulations with known effects on the real covariates of 60 city-regions (assumption checks, not
validation of the real-data estimates). Vegetation response is explicit: NDVI = h(W) + a_c ISA + u.
HI = g_c(W) + theta_dir ISA + beta_c NDVI + U + eps  (ISA in units of ten percentage points).
Scenarios: A, no unmeasured confounding; B03/B05/B08, a spatially smooth unmeasured confounder U whose correlation
with the 2-km block mean of ISA is 0.3 (weak), 0.5 (moderate) or 0.8 (strong); C, nonlinear and heterogeneous."""
import sys, os, json, numpy as np, pandas as pd, lightgbm as lgb, warnings, time
from scipy.ndimage import gaussian_filter
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
NC, NCELL, REPS = 60, 3000, 5
THD = 0.05
SCEN = {'A': 0.0, 'B03': 0.3, 'B05': 0.5, 'B08': 0.8, 'C': 0.0}
OUT = f'{RES}/sim'; os.makedirs(OUT, exist_ok=True)
SP = dict(E.NP); SR = 100


def smooth_field(dx, dy, rng, scale_km=3.0):
    gx = ((dx - dx.min()) / 0.5).astype(int); gy = ((dy - dy.min()) / 0.5).astype(int)
    z = gaussian_filter(rng.standard_normal((gy.max() + 1, gx.max() + 1)), scale_km / 0.5)
    v = z[gy, gx]; return (v - v.mean()) / v.std()


def gbm_effect(d, F, y, folds, shift=None):
    eff = np.full(len(d), np.nan)
    for f in np.unique(folds):
        tr, te = folds != f, folds == f
        m = lgb.train(SP, lgb.Dataset(d.loc[tr, F], y[tr], categorical_feature=['bin5']), SR)
        X1 = d.loc[te, F].copy(); p0 = m.predict(X1); X1['D'] = np.minimum(X1.D + 1, 10)
        if shift: X1['N'] = X1.N + shift
        eff[te] = m.predict(X1) - p0
    return float(np.mean(eff))


def one_city(c, clim, own):
    s = slug(c); fo = f'{OUT}/{s}.json'
    if os.path.exists(fo): return 'skip'
    h = pd.read_parquet(f'{DATA}/hi/{s}.parquet').dropna(subset=['hi3', 'wc_built', 'ndvi3', 'wc_tree'] + E.TERRAIN)
    if len(h) < NCELL + 5000: return 'small'
    rng = np.random.default_rng(abs(hash(c)) % 2 ** 32)
    idx = rng.permutation(len(h)); d = h.iloc[idx[:NCELL]].reset_index(drop=True); aux = h.iloc[idx[NCELL:NCELL + 8000]]
    d['bin5'] = ((np.floor(d.dx / 5) + 20) * 100 + np.floor(d.dy / 5) + 20).astype(int)
    d['blk2'] = ((np.floor(d.dx / 2) + 50) * 1000 + np.floor(d.dy / 2) + 50).astype(int)
    d['D'] = d.wc_built * 10
    g = lgb.train(SP, lgb.Dataset(aux[E.TERRAIN], aux.hi3), SR).predict(d[E.TERRAIN])
    hN = lgb.train(SP, lgb.Dataset(aux[E.TERRAIN], aux.ndvi3), SR).predict(d[E.TERRAIN])
    a_c = float(own.loc[c, 'cs3_a_ndvi3']); beta = -6.0 * float(np.clip(clim.loc[c, 'aridity'], 0.25, 1.5))
    u_pool = (d.ndvi3 - hN - a_c * d.D).values
    sig = float(np.std(d.hi3 - g)) * 0.8
    bm = d.groupby('blk2').D.transform('mean').values; bm = (bm - bm.mean()) / (bm.std() + 1e-9)
    folds = E.folds_by_block(d.blk2.values); W = E.TERRAIN + ['bin5']
    out = []
    for sc, rho in SCEN.items():
        for r in range(REPS):
            u = rng.permutation(u_pool); N = hN + a_c * d.D.values + u
            U = np.zeros(len(d))
            if rho > 0:
                F_ = smooth_field(d.dx.values, d.dy.values, rng); U = rho * bm + np.sqrt(1 - rho ** 2) * F_; U = U / U.std() * 1.0
            if sc == 'C':
                thd = THD + 0.2 * d.wc_tree.values; gam = 4.0
                HI = g + thd * d.D.values + beta * N + gam * (N - 0.4) ** 2 + rng.normal(0, sig, len(d))
                true_tot = float(np.mean(thd + (beta + 2 * gam * (N - 0.4)) * a_c)); true_dir = float(np.mean(thd))
            else:
                HI = g + THD * d.D.values + beta * N + U + rng.normal(0, sig, len(d))
                true_tot = THD + beta * a_c; true_dir = THD
            d['Y'] = HI; d['N'] = N
            o = E.dml(d, 'Y', 'D', W, cat=['bin5'], mediators=('N',), folds=folds)
            res = dict(city=c, scen=sc, rep=r, true_total=true_tot, true_direct=true_dir,
                       dml_total=o['theta'], dml_total_se=o['se'], dml_direct=o['direct'], dml_direct_se=o['direct_se'])
            res['gbm_min_bins'] = gbm_effect(d, ['D'] + W, HI, folds)
            res['gbm_full_bins'] = gbm_effect(d, ['D', 'N'] + W, HI, folds)
            res['gbm_full_bins_joint'] = gbm_effect(d, ['D', 'N'] + W, HI, folds, shift=a_c)
            res['gbm_min_nobins'] = gbm_effect(d.assign(bin5=0), ['D'] + W, HI, folds)
            out.append(res)
    json.dump(out, open(fo, 'w')); return len(out)


if __name__ == '__main__':
    clim = pd.read_csv(f'{RES}/city_climate.csv').set_index('city')
    own = pd.DataFrame([json.load(open(f)) for f in sorted(__import__('glob').glob(f'{RES}/city/*.json'))]).set_index('city')
    rng = np.random.default_rng(7); cs = list(rng.permutation(sorted(cities().city)))[:NC]
    part, npart = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    for c in cs[part::npart]:
        if c not in own.index: print(c, 'not yet', flush=True); continue
        t = time.time(); print(c, one_city(c, clim, own), round(time.time() - t, 1), flush=True)
