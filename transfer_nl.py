"""Nonlinear causal transfer model (R-learner with gradient boosting): tau(V) fitted by LightGBM on the pseudo-outcome
Yt/Dt with weights Dt^2 (Nie & Wager 2021), same modifiers as the linear model. Continent-out intervention test and
projection of the heat cost of sealing in fringe cells under CMIP6 climates (all-city fit)."""
import sys, numpy as np, pandas as pd, lightgbm as lgb, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import transfer as T
P = dict(objective='regression', learning_rate=0.05, num_leaves=15, min_data_in_leaf=2000, feature_fraction=0.9, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=10.0, verbose=-1, num_threads=2)
NR = 300


class NL:
    def fit(self, R):
        V = T.vmat(R, R.wc_tree.values, R.wc_built.values); dt = R.Dt.values
        m = np.abs(dt) > 0.05
        y = np.clip(R.Yt.values[m] / dt[m], -20, 20); w = dt[m] ** 2
        self.m = lgb.train(P, lgb.Dataset(V[m], y, weight=w), NR); return self

    def tau(self, V): return self.m.predict(V)


if __name__ == '__main__':
    I = T.build(); H, Rz, clim = I['H'], I['R'], I['clim']
    cs = np.array(sorted(Rz.city.unique())); cont = clim.loc[cs, 'region']; rows = []
    for r in cont.unique():
        test = list(cont[cont == r].index); mdl = NL().fit(Rz[~Rz.city.isin(test)])
        for c in test:
            h = H[H.city == c].dropna(subset=['isa3', 'tree3'])
            out = dict(city=c, nl_all=float(np.mean(mdl.tau(T.vmat(h, h.wc_tree.values, h.wc_built.values)))))
            u = h[h.nb1k_isa >= 0.1]
            if len(u) >= 50: out['nl_urban'] = float(np.mean(mdl.tau(T.vmat(u, u.wc_tree.values, u.wc_built.values))))
            rows.append(out)
        print(r, flush=True)
    pd.DataFrame(rows).to_csv(f'{RES}/transfer_nonlinear.csv', index=False)
    # projection with the all-city fit
    mdl = NL().fit(Rz); D = pd.read_csv(f'{RES}/cmip6_deltas.csv'); pr = []
    for c in cs:
        h = H[H.city == c]; f = h[(h.nb1k_isa >= 0.1) & (h.nb1k_isa < 0.5)]
        if len(f) < 100: f = h
        f = f.sample(min(len(f), 2000), random_state=0)
        def tau(cl):
            g = f.copy()
            for v in T.CLIM: g[v] = cl[v]
            return float(np.mean(mdl.tau(T.vmat(g, g.wc_tree.values, g.wc_built.values))))
        t0 = tau({v: clim.loc[c, v] for v in T.CLIM})
        for _, r in D[D.city == c].iterrows():
            t1 = tau(dict(aridity=r.aridity_f, tmax_warm=r.tmax_warm_f, vpd_warm=r.vpd_warm_f, soil=r.soil_f, ws=r.ws_f))
            pr.append(dict(city=c, model=r.model, scen=r.scen, period=r.period, tau0=t0, d_tau_nl=t1 - t0))
    pd.DataFrame(pr).to_csv(f'{RES}/projection_nonlinear.csv', index=False)
    print(pd.DataFrame(pr).groupby(['scen', 'period']).d_tau_nl.median())
