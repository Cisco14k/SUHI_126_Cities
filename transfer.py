"""Transfer of sealing effects to held-out cities: causal transfer model (linear R-learner on within-city DML
residuals with climate and cell modifiers) versus pooled gradient boosting with several conditioning sets.
(a) prediction of 1985-1989 -> 2021-2025 change of heat-island intensity in changing cells;
(b) intervention: +10 percentage points of impervious cover with everything else fixed (continent-out);
(c) city-level transferred effects and intervals; (d) split-conformal intervals for single cells."""
import sys, os, json, glob, numpy as np, pandas as pd, lightgbm as lgb, warnings
from scipy.stats import spearmanr
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
CLIM = ['aridity', 'tmax_warm', 'vpd_warm', 'soil', 'ws']
GP = dict(objective='regression', learning_rate=0.07, num_leaves=63, min_data_in_leaf=100, feature_fraction=0.8, bagging_fraction=0.8,
          bagging_freq=1, lambda_l2=1.0, max_bin=127, verbose=-1, num_threads=1)
GR = 300
SETS = {'full': ['isa', 'ndvi', 'albedo', 'tree'] + E.TERRAIN + CLIM,
        'partial': ['isa', 'tree'] + E.TERRAIN + CLIM,
        'minimal': ['isa'] + E.TERRAIN + CLIM,
        'full_loc': ['isa', 'ndvi', 'albedo', 'tree'] + E.TERRAIN + CLIM + ['dx', 'dy', 'dist'],
        'minimal_loc': ['isa'] + E.TERRAIN + CLIM + ['dx', 'dy', 'dist'],
        'full_mono': ['isa', 'ndvi', 'albedo', 'tree'] + E.TERRAIN + CLIM}
VMOD = ['tree', 'isa_cell', 'ndvi_rural', 'log_aridity', 'tmax_warm', 'vpd_warm', 'log_soil', 'ws']


def build():
    fn = f'{RES}/transfer_inputs.pkl'
    if os.path.exists(fn): return pd.read_pickle(fn)
    clim = pd.read_csv(f'{RES}/city_climate.csv').set_index('city')
    own = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city/*.json')]).set_index('city')
    H, Rz = [], []
    for c in own.index:
        s = slug(c); h = pd.read_parquet(f'{DATA}/hi/{s}.parquet'); h['city'] = c
        h['ndvi_rural'] = np.nanmedian(h.loc[h.nb1k_isa < 0.05, 'ndvi3']) if (h.nb1k_isa < 0.05).sum() > 100 else np.nanmedian(h.ndvi3)
        for v in CLIM: h[v] = clim.loc[c, v]
        H.append(h)
        r = pd.read_parquet(f'{DATA}/hi/{s}_resid.parquet'); r['city'] = c; r['ndvi_rural'] = h.ndvi_rural.iloc[0]
        for v in CLIM: r[v] = clim.loc[c, v]
        Rz.append(r)
    H = pd.concat(H, ignore_index=True); Rz = pd.concat(Rz, ignore_index=True)
    out = dict(H=H, R=Rz, own=own, clim=clim); pd.to_pickle(out, fn); return out


def vmat(df, tree, isa_cell):
    return pd.DataFrame({'tree': tree, 'isa_cell': isa_cell, 'ndvi_rural': df.ndvi_rural.values, 'log_aridity': np.log(df.aridity.values),
                         'tmax_warm': df.tmax_warm.values, 'vpd_warm': df.vpd_warm.values, 'log_soil': np.log1p(df.soil.values), 'ws': df.ws.values})


class Causal:
    """tau(V) = [1, Vstd] beta; ridge on Z = [1, Vstd] * Dt, lambda by city-grouped CV."""
    def fit(self, R, lams=(0.1, 1, 10, 100, 1000)):
        V = vmat(R, R.wc_tree.values, R.wc_built.values); self.mu, self.sd = V.mean(), V.std() + 1e-9
        Z = np.column_stack([np.ones(len(R)), ((V - self.mu) / self.sd).values]) * R.Dt.values[:, None]; y = R.Yt.values
        cs = R.city.unique(); rng = np.random.default_rng(0); fo = dict(zip(rng.permutation(cs), np.arange(len(cs)) % 5)); f = R.city.map(fo).values
        best = None
        for lam in lams:
            err = 0
            for k in range(5):
                b = self._ridge(Z[f != k], y[f != k], lam); err += ((y[f == k] - Z[f == k] @ b) ** 2).sum()
            if best is None or err < best[1]: best = (lam, err)
        self.lam = best[0]; self.beta = self._ridge(Z, y, self.lam); return self

    @staticmethod
    def _ridge(Z, y, lam):
        P = np.eye(Z.shape[1]) * lam; P[0, 0] = 0
        return np.linalg.solve(Z.T @ Z + P, Z.T @ y)

    def tau(self, V):
        Vs = ((V - self.mu) / self.sd).values; return self.beta[0] + Vs @ self.beta[1:]


def gbm_rows(H, k):
    return pd.DataFrame({'isa': H[f'isa{k}'], 'ndvi': H[f'ndvi{k}'], 'albedo': H[f'albedo{k}'], 'tree': H[f'tree{k}'],
                         **{w: H[w] for w in E.TERRAIN + CLIM + ['dx', 'dy', 'dist']}, 'hi': H[f'hi{k}'], 'city': H.city})


def fit_gbms(H, train, sets=SETS, n=1000):
    T = H[H.city.isin(train)]
    T = T.groupby('city', group_keys=False)[T.columns].apply(lambda x: x.sample(min(len(x), n), random_state=1))
    X = pd.concat([gbm_rows(T, 0), gbm_rows(T, 3)], ignore_index=True).dropna()
    M = {}
    for nm, F in sets.items():
        p = dict(GP)
        if nm == 'full_mono': p['monotone_constraints'] = [1 if f == 'isa' else 0 for f in F]
        M[nm] = (lgb.train(p, lgb.Dataset(X[F], X.hi), GR), F)
    return M


def changing(H, c, nmax=3000):
    h = H[H.city == c].dropna(subset=['hi0', 'hi3', 'isa0', 'isa3', 'ndvi0', 'ndvi3']).copy()
    h['dI'] = h.isa3 - h.isa0; h['dY'] = h.hi3 - h.hi0
    un = h.dI.abs() < 0.02
    if un.sum() < 100: return None, None
    ch = h[h.dI.abs() >= 0.05]
    if len(ch) < 100: return None, None
    ch = ch.sample(min(len(ch), nmax), random_state=0); ch['dYrel'] = ch.dY - h.loc[un, 'dY'].median()
    return ch, h[un].sample(min(un.sum(), 2000), random_state=0)


def predict_change(models, causal, ch, un):
    out = {}
    V = vmat(ch, (ch.tree0 + ch.tree3) / 2, (ch.isa0 + ch.isa3) / 2)
    out['causal'] = causal.tau(V) * ch.dI.values * 10
    for nm, (m, F) in models.items():
        f = lambda d: m.predict(gbm_rows(d, 3)[F]) - m.predict(gbm_rows(d, 0)[F])
        out[nm] = f(ch) - np.median(f(un))
    return out


def metrics(y, p):
    ok = np.isfinite(y) & np.isfinite(p)
    y, p = y[ok], p[ok]; rho = spearmanr(y, p).correlation
    r2 = 1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum(); slope = np.cov(p, y)[0, 1] / max(np.var(p), 1e-9)
    return rho, r2, slope


def intervention(models, causal, H, c, a_med):
    h = H[(H.city == c)].dropna(subset=['isa3', 'ndvi3', 'albedo3', 'tree3', 'hi3'])
    res = {}
    for scope, m in [('all', np.ones(len(h), bool)), ('urban', h.nb1k_isa.values >= 0.1)]:
        if m.sum() < 50: continue
        d = h[m]; X0 = gbm_rows(d, 3)
        res[f'causal_{scope}'] = float(np.mean(causal.tau(vmat(d, d.wc_tree.values, d.wc_built.values))))
        for nm, (mdl, F) in models.items():
            X1 = X0.copy(); X1['isa'] = np.minimum(X1.isa + 0.1, 1); p0 = mdl.predict(X0[F])
            res[f'{nm}_{scope}'] = float(np.mean(mdl.predict(X1[F]) - p0))
            if nm == 'full':
                for mc, ac in [('ndvi', 'ndvi3'), ('albedo', 'albedo3'), ('tree', 'wc_tree')]: X1[mc] = X1[mc] + a_med[ac]
                X1['tree'] = X1.tree.clip(0, 1); res[f'full_joint_{scope}'] = float(np.mean(mdl.predict(X1[F]) - p0))
    return res


def run(only=None):
    I = build(); H, Rz, own, clim = I['H'], I['R'], I['own'], I['clim']
    cs = np.array(sorted(own.index)); rng = np.random.default_rng(42)
    zone = clim.loc[cs, 'zone']; cont = clim.loc[cs, 'region']
    perm = rng.permutation(cs); six = {c: i // 6 for i, c in enumerate(perm)}
    designs = {'six': [[c for c in cs if six[c] == f] for f in sorted(set(six.values()))],
               'zone': [list(zone[zone == z].index) for z in zone.unique()],
               'continent': [list(cont[cont == r].index) for r in cont.unique()]}
    rows, inter, cityeff, resid_store = [], [], [], {}
    for dn, folds in designs.items():
        if only and dn not in only: continue
        for fi, test in enumerate(folds):
            train = [c for c in cs if c not in test]
            causal = Causal().fit(Rz[Rz.city.isin(train)])
            models = fit_gbms(H, train, SETS if dn != 'zone' else {k: SETS[k] for k in ['full', 'partial', 'minimal']})
            a_med = {}
            for ac in ['ndvi3', 'albedo3', 'wc_tree']:
                a_med[ac] = own.loc[train].groupby(clim.loc[train, 'zone'])[f'cs3_a_{ac}'].median()
            for c in test:
                ch, un = changing(H, c)
                if ch is not None:
                    P = predict_change(models, causal, ch, un)
                    for nm, p in P.items():
                        rho, r2, sl = metrics(ch.dYrel.values, p)
                        rows.append(dict(design=dn, fold=fi, city=c, model=nm, rho=rho, r2=r2, slope=sl, n=len(ch)))
                        if dn == 'six': resid_store[(c, nm)] = (ch.dYrel.values - p, np.abs(p))
                    ur = ch.nb1k_isa.values >= 0.1
                    if ur.sum() >= 50:
                        for nm, p in P.items():
                            rho, r2, sl = metrics(ch.dYrel.values[ur], p[ur])
                            rows.append(dict(design=dn + '_urban', fold=fi, city=c, model=nm, rho=rho, r2=r2, slope=sl, n=int(ur.sum())))
                if dn == 'continent':
                    z = clim.loc[c, 'zone']; am = {ac: a_med[ac].get(z, np.nanmedian(a_med[ac])) for ac in a_med}
                    r = intervention(models, causal, H, c, am); r['city'] = c
                    tz = own.loc[train][clim.loc[train, 'zone'] == z]['cs3_theta']
                    r['zone_baseline'] = float(tz.median()) if len(tz) else float(own.loc[train, 'cs3_theta'].median())
                    inter.append(r)
                if dn == 'six':
                    h = H[H.city == c].dropna(subset=['isa3', 'tree3'])
                    cityeff.append(dict(city=c, tau_six=float(np.mean(causal.tau(vmat(h, h.wc_tree.values, h.wc_built.values))))))
            print(dn, fi, len(rows), flush=True)
    tag = '_'.join(only) if only else 'all'
    pd.to_pickle(dict(rows=rows, inter=inter, cityeff=cityeff, resid=resid_store), f'{RES}/transfer_part_{tag}.pkl')


def merge():
    import glob as g
    P = [pd.read_pickle(f) for f in sorted(g.glob(f'{RES}/transfer_part_*.pkl'))]
    clim = pd.read_csv(f'{RES}/city_climate.csv').set_index('city')
    pd.DataFrame(sum([p['rows'] for p in P], [])).to_csv(f'{RES}/transfer_change.csv', index=False)
    pd.DataFrame(sum([p['inter'] for p in P], [])).to_csv(f'{RES}/transfer_intervention.csv', index=False)
    pd.DataFrame(sum([p['cityeff'] for p in P], [])).to_csv(f'{RES}/transfer_cityeff.csv', index=False)
    store = {}
    for p in P: store.update(p['resid'])
    pd.to_pickle(store, f'{RES}/transfer_resid.pkl'); conformal(store, clim)


def conformal(store, clim):
    """Split-conformal 90% intervals with city-level exchangeability: quantile of |residual| over all other
    cities (global) or over the other cities of the same continent (group-conditional)."""
    rows = []
    for nm in ['causal', 'full', 'minimal']:
        cs = sorted({c for (c, m) in store if m == nm})
        for c in cs:
            others = [store[(o, nm)][0] for o in cs if o != c]
            q = np.quantile(np.abs(np.concatenate(others)), 0.9)
            same = [store[(o, nm)][0] for o in cs if o != c and clim.loc[o, 'region'] == clim.loc[c, 'region']]
            qg = np.quantile(np.abs(np.concatenate(same)), 0.9) if same else np.nan
            r = store[(c, nm)][0]
            rows.append(dict(city=c, model=nm, region=clim.loc[c, 'region'], q90=q, cover=float(np.mean(np.abs(r) <= q)),
                             q90_group=qg, cover_group=float(np.mean(np.abs(r) <= qg))))
    pd.DataFrame(rows).to_csv(f'{RES}/conformal.csv', index=False)


if __name__ == '__main__':
    if sys.argv[1:] == ['merge']: merge()
    elif sys.argv[1:] == ['build']: build()
    else: run(sys.argv[1:] or None)
