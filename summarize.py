"""Pool within-city estimates and transfer results; write results/summary.json and tables used in text and figures."""
import sys, json, glob, numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
ZONES = ['Tropical', 'Arid', 'Temperate', 'Continental']


def load_own():
    own = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city/*.json')]).set_index('city')
    clim = pd.read_csv(f'{RES}/city_climate.csv').set_index('city')
    return own.join(clim[['zone', 'region', 'country', 'koppen_ms', 'lat', 'lon', 'aridity', 'tmax_warm']]), clim


def pool(own, est, se, by_zone=True):
    out = {'All': E.re_pool(own[est], own[se])}
    out['All_noPolar'] = E.re_pool(own.loc[own.zone != 'Polar', est], own.loc[own.zone != 'Polar', se])
    if by_zone:
        for z in ZONES: out[z] = E.re_pool(own.loc[own.zone == z, est], own.loc[own.zone == z, se])
    return out


def boot_ci(x, f, n=2000, seed=0):
    x = np.asarray(x); rng = np.random.default_rng(seed); v = [f(x[rng.integers(0, len(x), len(x))]) for _ in range(n)]
    return float(f(x)), float(np.nanquantile(v, 0.025)), float(np.nanquantile(v, 0.975))


if __name__ == '__main__':
    own, clim = load_own(); S = {'n_cities': len(own)}
    S['zone_counts'] = own.zone.value_counts().to_dict()
    est = {'total_wc': ('cs3_theta', 'cs3_se'), 'direct': ('cs3_direct', 'cs3_direct_se'), 'path_ndvi': ('cs3_path_ndvi3', 'cs3_path_ndvi3_se'),
           'path_albedo': ('cs3_path_albedo3', 'cs3_path_albedo3_se'), 'path_tree_joint': ('cs3_path_wc_tree', 'cs3_path_wc_tree_se'),
           'path_tree_only': ('cs3t_path_tree', 'cs3t_path_tree_se'), 'direct_tree_only': ('cs3t_direct', 'cs3t_direct_se'),
           'total_nobins': ('cs3_theta_nobins', 'cs3_se_nobins'), 'nco': ('nco_theta', 'nco_se'),
           'core': ('st_core_theta', 'st_core_se'), 'fringe': ('st_fringe_theta', 'st_fringe_se'), 'rural': ('st_rural_theta', 'st_rural_se')}
    for k in range(4): est[f'bc{k}'] = (f'bc{k}_theta', f'bc{k}_se'); est[f'bc{k}_direct'] = (f'bc{k}_direct', f'bc{k}_direct_se')
    for p in ['03', '13', '23', '01', '12']: est[f'fd{p}'] = (f'fd{p}_theta', f'fd{p}_se')
    for d in ['cciA', 'cciB', 'bcA', 'bcB']:
        for pn in ['pre2', 'pre1', 'post', 'post2']: est[f'{d}_{pn}'] = (f'{d}_{pn}_theta', f'{d}_{pn}_se')
    for nm, (e, s) in est.items():
        if e in own: S[nm] = pool(own, e, s)
    S['total_positive'] = int((own.cs3_theta > 0).sum()); S['total_sig_pos'] = int((own.cs3_theta - 1.96 * own.cs3_se > 0).sum())
    S['total_sig_neg'] = int((own.cs3_theta + 1.96 * own.cs3_se < 0).sum())
    S['median_total'] = float(own.cs3_theta.median()); S['median_direct'] = float(own.cs3_direct.median())
    S['share_path_ndvi'] = float(S['path_ndvi']['All']['mu'] / S['total_wc']['All']['mu'])
    S['share_path_tree_only'] = float(S['path_tree_only']['All']['mu'] / S['total_wc']['All']['mu'])
    S['overlap_r2_DW_median'] = float(own.cs3_r2_DW.median()); S['overlap_r2_DW_q90'] = float(own.cs3_r2_DW.quantile(0.9))
    S['rv_median'] = float(own.sens_rv.median()); S['rv_alpha_median'] = float(own.sens_rv_alpha.median())
    S['sens_adj_pool'] = E.re_pool(own.sens_theta_adj_1x, own.cs3_se)
    S['sens_sign_survive'] = int(((own.sens_theta_adj_1x > 0) & (own.cs3_theta > 0)).sum())
    S['sens_bias_median'] = float(own.sens_bias_1x.median())
    S['nco_sig'] = int(((own.nco_theta - 1.96 * own.nco_se) > 0).sum()); S['nco_n'] = int(own.nco_theta.notna().sum())
    S['gbm_within'] = {k: boot_ci(own[k].dropna(), np.median) for k in ['gbm_min_eff', 'gbm_full_eff', 'gbm_full_joint_eff', 'cs3_theta', 'cs3_direct']}
    S['gbm_within_mae_total'] = {k: boot_ci((own[k] - own.cs3_theta).abs().dropna(), np.mean) for k in ['gbm_min_eff', 'gbm_full_eff', 'gbm_full_joint_eff']}
    S['gbm_within_mae_direct'] = {k: boot_ci((own[k] - own.cs3_direct).abs().dropna(), np.mean) for k in ['gbm_min_eff', 'gbm_full_eff', 'gbm_full_joint_eff']}
    S['urban_share_median'] = float(own.urban_share.median()); S['fringe_share_median'] = float(own.fringe_share.median())
    S['lapse_median'] = float(pd.concat([own[f'lapse{k}'] for k in range(4)]).median())
    S['uhi_core'] = {k: float(own[f'uhi_core{k}'].median()) for k in range(4)}
    bc = pd.read_csv(f'{RES}/backcast_cv.csv'); S['backcast_cv'] = bc.drop(columns='city').median().to_dict()
    try:
        bt = pd.read_csv(f'{RES}/backcast_temporal.csv'); S['backcast_temporal'] = bt.drop(columns='city').median().to_dict()
        S['backcast_temporal_n_lcmap'] = int(bt.lc_lev3.notna().sum()) if 'lc_lev3' in bt else 0
    except FileNotFoundError: pass
    # transfer: prediction of change
    T = pd.read_csv(f'{RES}/transfer_change.csv'); S['change'] = {}
    for (dsg, m), g in T.groupby(['design', 'model']):
        S['change'][f'{dsg}|{m}'] = dict(rho=boot_ci(g.rho.dropna(), np.median), r2=boot_ci(g.r2.dropna(), np.median), slope=boot_ci(g.slope.dropna(), np.median), n=int(len(g)))
    six = T[T.design == 'six'].pivot(index='city', columns='model', values='rho')
    S['causal_beats_full_share'] = float((six.causal > six.full).mean()); S['n_changing_cells'] = int(T[(T.design == 'six') & (T.model == 'causal')].n.sum())
    # intervention
    I = pd.read_csv(f'{RES}/transfer_intervention.csv').set_index('city').join(own[['cs3_theta', 'cs3_direct', 'cs3_se', 'zone', 'region']])
    S['intervention'] = {}
    for c in [x for x in I.columns if x.endswith('_all') or x.endswith('_urban')] + ['zone_baseline']:
        x = I[[c, 'cs3_theta', 'cs3_direct']].dropna()
        idx = np.arange(len(x))
        S['intervention'][c] = dict(
            median=boot_ci(x[c].values, np.median),
            mae_total=boot_ci(idx, lambda i: np.mean(np.abs(x[c].values[i] - x.cs3_theta.values[i]))),
            mae_direct=boot_ci(idx, lambda i: np.mean(np.abs(x[c].values[i] - x.cs3_direct.values[i]))),
            sign=boot_ci(idx, lambda i: np.mean(np.sign(x[c].values[i]) == np.sign(x.cs3_theta.values[i]))),
            rho=boot_ci(idx, lambda i: spearmanr(x[c].values[i], x.cs3_theta.values[i]).correlation), n=len(x))
    # city-level transferred effects vs own (six-out)
    C = pd.read_csv(f'{RES}/transfer_cityeff.csv').set_index('city').join(own[['cs3_theta', 'cs3_se', 'fd03_theta', 'fd03_se']])
    C = C.dropna(subset=['tau_six', 'cs3_theta']); dev = (C.tau_six - C.cs3_theta).abs().values
    q = np.array([np.quantile(np.delete(dev, i), 0.9) for i in range(len(dev))])
    S['city_interval'] = dict(halfwidth=float(np.median(q)), coverage=float(np.mean(dev <= q)), sd_own=float(C.cs3_theta.std()),
                              rho_cs=float(spearmanr(C.tau_six, C.cs3_theta).correlation),
                              rho_fd=float(spearmanr(C.tau_six, C.fd03_theta, nan_policy='omit').correlation),
                              within_own_ci=float(np.mean(np.abs(C.tau_six - C.cs3_theta) <= 1.96 * C.cs3_se)))
    K = pd.read_csv(f'{RES}/conformal.csv'); S['conformal'] = {m: dict(q90=float(g.q90.median()), cover=float(g.cover.median()), cover_group=float(g.cover_group.median()),
                                                                 cover_by_region=g.groupby('region').cover.median().to_dict(), cover_group_by_region=g.groupby('region').cover_group.median().to_dict())
                                                              for m, g in K.groupby('model')}
    # simulations
    try:
        sim = pd.concat([pd.DataFrame(json.load(open(f))) for f in glob.glob(f'{RES}/sim/*.json')], ignore_index=True)
        sim['cover'] = (np.abs(sim.dml_total - sim.true_total) <= 1.96 * sim.dml_total_se)
        sim['cover_dir'] = (np.abs(sim.dml_direct - sim.true_direct) <= 1.96 * sim.dml_direct_se)
        S['sim'] = {}
        for sc, g in sim.groupby('scen'):
            r = dict(n=len(g), ncity=g.city.nunique(), true_total=float(g.true_total.median()), true_direct=float(g.true_direct.median()),
                     cover_total=float(g.cover.mean()), cover_direct=float(g.cover_dir.mean()),
                     rho_dml=float(spearmanr(g.groupby('city').dml_total.mean(), g.groupby('city').true_total.mean()).correlation))
            for e_ in ['dml_total', 'dml_direct', 'gbm_min_bins', 'gbm_full_bins', 'gbm_full_bins_joint', 'gbm_min_nobins']:
                tgt = g.true_direct if e_ in ('dml_direct', 'gbm_full_bins') else g.true_total
                r[e_] = dict(median=float(g[e_].median()), bias=float((g[e_] - tgt).mean()), rmse=float(np.sqrt(((g[e_] - tgt) ** 2).mean())),
                             bias_vs_total=float((g[e_] - g.true_total).mean()))
            S['sim'][sc] = r
        sim.to_csv(f'{RES}/sim_all.csv', index=False)
    except ValueError: pass
    # projections
    try:
        P = pd.read_csv(f'{RES}/projection.csv'); F = P[P.scen != 'present']
        S['proj'] = {}
        for (sc, pe), g in F.groupby(['scen', 'period']):
            cm = g.groupby('city').agg(d_tau_alt=('d_tau_alt', 'median'), d_tau=('d_tau', 'median'), dT=('dtmax_warm', 'median'), ex=('extrap', 'max'), lo=('d_tau', 'min'), hi=('d_tau', 'max'))
            S['proj'][f'{sc}|{pe}'] = dict(d_tau_alt_median=float(cm.d_tau_alt.median()), d_tau_alt_q90=float(cm.d_tau_alt.quantile(.9)), d_tau_alt_q10=float(cm.d_tau_alt.quantile(.1)), d_tau_median=float(cm.d_tau.median()), d_tau_q25=float(cm.d_tau.quantile(.25)), d_tau_q75=float(cm.d_tau.quantile(.75)),
                                           dT_median=float(cm.dT.median()), share_extrap=float((cm.ex > 0).mean()), share_increase=float((cm.d_tau > 0).mean()),
                                           share_gcm_agree=float(((cm.lo > 0) | (cm.hi < 0)).mean()),
                                           by_zone=g.merge(clim[['zone']], left_on='city', right_index=True, suffixes=('', '_c')).groupby('zone').d_tau.median().to_dict())
        S['proj_present_median'] = float(P[P.scen == 'present'].tau.median())
    except FileNotFoundError: pass
    json.dump(S, open(f'{RES}/summary.json', 'w'), indent=1, default=float)
    print(json.dumps({k: S[k] for k in ['n_cities', 'total_wc', 'direct', 'path_ndvi', 'path_tree_only']}, indent=0, default=float)[:3000])
