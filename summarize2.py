"""Round-3 summaries added to results/summary.json under key 'r3'."""
import sys, json, glob, pickle, numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
from summarize import load_own, boot_ci
PURPOSIVE = ['Chengdu', 'Kashgar', 'Lhasa', 'Nanjing', 'Qingdao', 'Shenzhen', 'Koforidua', 'Yendi', 'Fortaleza', 'Port Moresby', 'Toronto']

S = json.load(open(f'{RES}/summary.json')); own, clim = load_own(); R3 = {}
X = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city_extra/*.json')]).set_index('city')
X = X.join(own[['zone']])
for k in ['lag_unsealed', 'lag_unsealed_ref', 'lag_all', 'lag_all_ref', 'inner']:
    R3[k] = E.re_pool(X[f'{k}_theta'], X[f'{k}_se'])
R3['sp_own'] = E.re_pool(X.sp_own, X.sp_own_se); R3['sp_nb'] = E.re_pool(X.sp_nb, X.sp_nb_se); R3['sp_corr'] = float(X.sp_corr.median())
for d in ['cA', 'cB']:
    for pn in ['pre2', 'pre1', 'post', 'post2']:
        if f'{d}_{pn}_theta' in X: R3[f'{d}_{pn}'] = E.re_pool(X[f'{d}_{pn}_theta'], X[f'{d}_{pn}_se'])
    R3[f'{d}_ntreated_median'] = float(X[f'{d}_ntreated'].median())
R3['cal_slope'] = float(X.cal_slope.median()); R3['cal_slope_iqr'] = [float(X.cal_slope.quantile(.25)), float(X.cal_slope.quantile(.75))]
R3['lag_zone'] = {z: E.re_pool(X.loc[X.zone == z, 'lag_unsealed_theta'], X.loc[X.zone == z, 'lag_unsealed_se']) for z in ['Tropical', 'Arid', 'Temperate', 'Continental']}
# trend-adjusted event-study contrasts
def adj(df, pre2, pre1, post):
    a = df[f'{post}_theta'] - df[f'{pre1}_theta']; sa = np.sqrt(df[f'{post}_se'] ** 2 + df[f'{pre1}_se'] ** 2)
    out = dict(parallel=E.re_pool(a, sa))
    if pre2:
        b = df[f'{post}_theta'] - 2 * df[f'{pre1}_theta'] + df[f'{pre2}_theta']; sb = np.sqrt(df[f'{post}_se'] ** 2 + 4 * df[f'{pre1}_se'] ** 2 + df[f'{pre2}_se'] ** 2)
        out['linear'] = E.re_pool(b, sb)
    return out
R3['adj'] = {'bcA': adj(own, None, 'bcA_pre1', 'bcA_post'), 'bcB': adj(own, 'bcB_pre2', 'bcB_pre1', 'bcB_post'),
             'cciA': adj(own, None, 'cciA_pre1', 'cciA_post'), 'cciB': adj(own, 'cciB_pre2', 'cciB_pre1', 'cciB_post'),
             'cA': adj(X, None, 'cA_pre1', 'cA_post')}
if 'cB_pre2_theta' in X: R3['adj']['cB'] = adj(X, 'cB_pre2', 'cB_pre1', 'cB_post')
# excluding purposive and replaced cities
m = ~own.index.isin(PURPOSIVE); R3['excl_purposive'] = E.re_pool(own.loc[m, 'cs3_theta'], own.loc[m, 'cs3_se']); R3['n_excl'] = int((~m).sum())
# simulation-calibrated standard errors
sim = pd.read_csv(f'{RES}/sim_all.csv'); A = sim[sim.scen == 'A']
k = float(np.quantile(np.abs((A.dml_total - A.true_total) / A.dml_total_se), 0.95) / 1.96); R3['se_inflation'] = k
kC = float(np.quantile(np.abs((sim[sim.scen == 'C'].dml_total - sim[sim.scen == 'C'].true_total) / sim[sim.scen == 'C'].dml_total_se), 0.95) / 1.96); R3['se_inflation_C'] = kC
R3['total_calibrated'] = E.re_pool(own.cs3_theta, own.cs3_se * k)
R3['sig_pos_calibrated'] = int((own.cs3_theta - 1.96 * k * own.cs3_se > 0).sum()); R3['sig_neg_calibrated'] = int((own.cs3_theta + 1.96 * k * own.cs3_se < 0).sum())
# decision relevance: tercile agreement and identification of the top third of cities
I = pd.read_csv(f'{RES}/transfer_intervention.csv').set_index('city').join(own[['cs3_theta']])
NLr = pd.read_csv(f'{RES}/transfer_nonlinear.csv').set_index('city'); I = I.join(NLr)
terc = lambda x: pd.qcut(x.rank(method='first'), 3, labels=False)
R3['decision'] = {}
for c in ['causal_all', 'nl_all', 'full_all', 'partial_all', 'minimal_all', 'full_loc_all', 'minimal_loc_all', 'full_mono_all', 'full_joint_all', 'zone_baseline']:
    x = I[[c, 'cs3_theta']].dropna(); to, tm = terc(x.cs3_theta), terc(x[c]); idx = np.arange(len(x))
    R3['decision'][c] = dict(tercile_agree=boot_ci(idx, lambda i: np.mean(to.values[i] == tm.values[i])),
                             top_recall=float(np.mean(tm[to == 2] == 2)),
                             gross_misclass=float(np.mean(np.abs(to.values - tm.values) == 2)),
                             mae=boot_ci(idx, lambda i: np.mean(np.abs(x[c].values[i] - x.cs3_theta.values[i]))),
                             rho=float(spearmanr(x[c], x.cs3_theta).correlation), median=float(x[c].median()))
# nonlinear projection
try:
    PN = pd.read_csv(f'{RES}/projection_nonlinear.csv')
    R3['proj_nl'] = {f'{s}|{p}': dict(median=float(g.groupby('city').d_tau_nl.median().median()), q10=float(g.groupby('city').d_tau_nl.median().quantile(.1)), q90=float(g.groupby('city').d_tau_nl.median().quantile(.9)))
                     for (s, p), g in PN.groupby(['scen', 'period'])}
except FileNotFoundError: pass
# overpass time (local solar time) by epoch
rows = []
cty = cities().set_index('city')
for c in cty.index:
    f = f'{DATA}/landsat/{slug(c)}_scenes.csv'
    try: sc = pd.read_csv(f)
    except FileNotFoundError: continue
    sc = sc[sc.ok]; t = pd.to_datetime(sc.datetime, utc=True, format='ISO8601')
    lst = (t.dt.hour + t.dt.minute / 60 + cty.loc[c, 'lon'] / 15) % 24
    for k_, g in lst.groupby(sc.epoch.values): rows.append(dict(city=c, epoch=k_, solar=float(g.median()), n=len(g)))
O = pd.DataFrame(rows); R3['overpass'] = O.groupby('epoch').solar.median().to_dict(); R3['scenes'] = O.groupby('epoch').n.median().to_dict()
# within-city change of the effect with epoch warm-season temperature (city fixed effects)
tc = pickle.load(open(f'{DATA}/terraclimate.pkl', 'rb')); rr = []
for c in own.index:
    s_ = tc[c]['tmax'].mean(['lat', 'lon']).to_series(); wm = [int(x) for x in clim.loc[c, 'warm_months'].split('-')]
    s_ = s_[s_.index.month.isin(wm)]
    for k_, (y0, y1) in enumerate(EPOCHS):
        v = s_[str(y0):str(min(y1, 2021))]
        if len(v) and np.isfinite(own.loc[c].get(f'bc{k_}_theta', np.nan)):
            rr.append(dict(city=c, k=k_, tmax=float(v.mean()), th=own.loc[c, f'bc{k_}_theta'], se=own.loc[c, f'bc{k_}_se'], nsc=O[(O.city == c) & (O.epoch == k_)].n.sum()))
Q = pd.DataFrame(rr); Q['tm'] = Q.tmax - Q.groupby('city').tmax.transform('mean'); Q['ty'] = Q.th - Q.groupby('city').th.transform('mean')
w = 1 / Q.se ** 2; b = float((w * Q.tm * Q.ty).sum() / (w * Q.tm ** 2).sum())
# city-cluster bootstrap
rng = np.random.default_rng(0); bs = []
ucs = Q.city.unique()
for _ in range(1000):
    pick = rng.choice(ucs, len(ucs)); q = pd.concat([Q[Q.city == c_] for c_ in pick]); ww = 1 / q.se ** 2
    bs.append((ww * q.tm * q.ty).sum() / (ww * q.tm ** 2).sum())
R3['temporal_climate_slope'] = [b, float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]; R3['temporal_tm_sd'] = float(Q.tm.std())
# effect of scene count on epoch estimates (within city)
Q['ns'] = Q.nsc - Q.groupby('city').nsc.transform('mean'); R3['scene_slope'] = float((w * Q.ns * Q.ty).sum() / (w * Q.ns ** 2).sum())
S['r3'] = R3
json.dump(S, open(f'{RES}/summary.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in R3.items() if k not in ('decision', 'adj', 'lag_zone')}, default=float, indent=0)[:3500])
print(json.dumps(R3['adj'], default=float)[:2500]); print(json.dumps(R3['decision'], default=float)[:3000])
