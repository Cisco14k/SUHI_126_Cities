"""Round-4 summaries: finer-location spillover, screening against benchmarks independent of the cross-sectional
own estimates (dated conversions), and results for European city-regions. Stored under S['r4']."""
import sys, json, glob, numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
from summarize import load_own, boot_ci
S = json.load(open(f'{RES}/summary.json')); own, clim = load_own(); R4 = {}
X = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city_extra/*.json')]).set_index('city')
X2 = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city_extra2/*.json')]).set_index('city')
for k in ['sp2_own', 'sp2_nb', 'tot2']: R4[k] = E.re_pool(X2[k], X2[f'{k}_se'])
# independent benchmarks: dated-conversion contrasts (conversion minus pre-period), per city
B = pd.DataFrame(index=own.index)
B['conc'] = X.cA_post_theta - X.cA_pre1_theta; B['conc_se'] = np.sqrt(X.cA_post_se ** 2 + X.cA_pre1_se ** 2); B['conc_n'] = X.cA_ntreated
B['cci'] = own.cciA_post_theta - own.cciA_pre1_theta; B['cci_se'] = np.sqrt(own.cciA_post_se ** 2 + own.cciA_pre1_se ** 2)
I = pd.read_csv(f'{RES}/transfer_intervention.csv').set_index('city').join(pd.read_csv(f'{RES}/transfer_nonlinear.csv').set_index('city')).join(own[['cs3_theta']]).join(B)
R4['ext'] = {}
for bench, mask in [('conc', I.conc_n >= 30), ('cci', I.cci_se < 0.1)]:
    J = I[mask & I[bench].notna()]; out = dict(n=int(len(J)))
    terc = lambda x: pd.qcut(x.rank(method='first'), 3, labels=False)
    tb = terc(J[bench])
    for c in ['cs3_theta', 'causal_all', 'nl_all', 'full_all', 'full_joint_all', 'partial_all', 'minimal_all', 'zone_baseline']:
        idx = np.arange(len(J))
        out[c] = dict(rho=boot_ci(idx, lambda i: spearmanr(J[c].values[i], J[bench].values[i]).correlation),
                      tercile=float(np.mean(terc(J[c]).values == tb.values)))
    R4['ext'][bench] = out
# European city-regions
eu = own.region == 'Europe'; R4['eu_n'] = int(eu.sum())
for k, (e, s) in {'eu_total': ('cs3_theta', 'cs3_se'), 'eu_direct': ('cs3_direct', 'cs3_direct_se'), 'eu_core': ('st_core_theta', 'st_core_se'), 'eu_fringe': ('st_fringe_theta', 'st_fringe_se')}.items():
    R4[k] = E.re_pool(own.loc[eu, e], own.loc[eu, s])
R4['eu_lag'] = E.re_pool(X.loc[X.index.isin(own.index[eu]), 'lag_all_theta'], X.loc[X.index.isin(own.index[eu]), 'lag_all_se'])
R4['eu_sp_nb'] = E.re_pool(X.loc[X.index.isin(own.index[eu]), 'sp_nb'], X.loc[X.index.isin(own.index[eu]), 'sp_nb_se'])
Ie = I[I.index.isin(own.index[eu])]
R4['eu_mae'] = {c: float(np.mean(np.abs(Ie[c] - Ie.cs3_theta))) for c in ['causal_all', 'full_all', 'minimal_all', 'zone_baseline']}
R4['eu_rho'] = {c: float(spearmanr(Ie[c], Ie.cs3_theta).correlation) for c in ['causal_all', 'full_all', 'minimal_all', 'zone_baseline']}
S['r4'] = R4; json.dump(S, open(f'{RES}/summary.json', 'w'), indent=1, default=float)
print(json.dumps(R4, default=float, indent=0)[:4000])
