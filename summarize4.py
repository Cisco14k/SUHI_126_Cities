"""Round-5 summaries under S['r5']: CCI-dosed concordant benchmark, lagged design in vegetated cells, benchmark-city selection."""
import sys, json, glob, numpy as np, pandas as pd
from scipy.stats import spearmanr, mannwhitneyu
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
from summarize import load_own, boot_ci
S = json.load(open(f'{RES}/summary.json')); own, clim = load_own(); R5 = {}
X3 = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city_extra3/*.json')]).set_index('city')
X = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city_extra/*.json')]).set_index('city')
for k in ['cc_pre1', 'cc_post', 'lagveg', 'lagveg_ref']: R5[k] = E.re_pool(X3[k], X3[f'{k}_se'])
net = X3.cc_post - X3.cc_pre1; nse = np.sqrt(X3.cc_post_se ** 2 + X3.cc_pre1_se ** 2); R5['cc_net'] = E.re_pool(net, nse)
I = pd.read_csv(f'{RES}/transfer_intervention.csv').set_index('city').join(pd.read_csv(f'{RES}/transfer_nonlinear.csv').set_index('city')).join(own[['cs3_theta', 'zone', 'region']])
I['ccnet'] = net; I['ntr'] = X3.ntr
J = I[(I.ntr >= 30) & I.ccnet.notna()]; out = dict(n=int(len(J)))
terc = lambda x: pd.qcut(x.rank(method='first'), 3, labels=False)
for c in ['cs3_theta', 'causal_all', 'nl_all', 'full_all', 'full_joint_all', 'partial_all', 'minimal_all', 'zone_baseline']:
    idx = np.arange(len(J)); out[c] = dict(rho=boot_ci(idx, lambda i: spearmanr(J[c].values[i], J.ccnet.values[i]).correlation), tercile=float(np.mean(terc(J[c]).values == terc(J.ccnet).values)))
R5['ext_ccidose'] = out
# selection of benchmark cities (back-cast-dosed concordant benchmark, >=30 treated cells)
sel = (X.cA_ntreated >= 30) & X.cA_post_theta.notna() & X.cA_pre1_theta.notna(); ins = own.index.isin(X.index[sel])
R5['sel_n'] = int(ins.sum())
R5['sel_zone_in'] = own.loc[ins, 'zone'].value_counts().to_dict(); R5['sel_zone_out'] = own.loc[~ins, 'zone'].value_counts().to_dict()
R5['sel_region_in'] = own.loc[ins, 'region'].value_counts().to_dict()
R5['sel_own_median_in'] = float(own.loc[ins, 'cs3_theta'].median()); R5['sel_own_median_out'] = float(own.loc[~ins, 'cs3_theta'].median())
R5['sel_p'] = float(mannwhitneyu(own.loc[ins, 'cs3_theta'], own.loc[~ins, 'cs3_theta']).pvalue)
R5['sel_pool_in'] = E.re_pool(own.loc[ins, 'cs3_theta'], own.loc[ins, 'cs3_se']); R5['sel_pool_out'] = E.re_pool(own.loc[~ins, 'cs3_theta'], own.loc[~ins, 'cs3_se'])
# causal-vs-full ranking advantage by region (own benchmark)
R5['rho_by_region'] = {r: dict(causal=float(spearmanr(g.causal_all, g.cs3_theta).correlation), full=float(spearmanr(g.full_all, g.cs3_theta).correlation)) for r, g in I.groupby('region')}
S['r5'] = R5; json.dump(S, open(f'{RES}/summary.json', 'w'), indent=1, default=float)
print(json.dumps({k: v for k, v in R5.items()}, default=float)[:3500])
