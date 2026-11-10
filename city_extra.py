"""Additional within-city analyses requested in review round 3:
(a) lagged-outcome adjustment: 2021-2025 total effect conditioning also on the 1985-1989 heat island (and ISA),
    in cells unsealed in 1985-1989 and in all cells; (b) spillover: own-cell versus 1-km neighbourhood sealing
    estimated jointly; (c) inner city-region (rdist <= 0.5); (d) concordant dating: conversions dated by both the
    back-cast and ESA CCI, with controls unconverted in both; (e) calibration slope of WorldCover ISA on the
    out-of-fold back-cast (scale of back-cast effects)."""
import sys, os, json, time, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
W0 = E.TERRAIN; WL = E.TERRAIN + E.LOC
OUT = f'{RES}/city_extra'; os.makedirs(OUT, exist_ok=True)


def run(c):
    s = slug(c); fo = f'{OUT}/{s}.json'
    if os.path.exists(fo): return 'skip'
    t0 = time.time()
    h = pd.read_parquet(f'{DATA}/hi/{s}.parquet')
    d = pd.read_parquet(f'{DATA}/cells2/{s}.parquet'); d = d[[x for x in ['cell', 'bin5', 'blk2', 'cci_urban_1992', 'cci_urban_2000', 'cci_urban_2014', 'cci_urban_2020'] if x in d]]
    df = h.merge(d, on='cell', how='left')
    for k in range(4):
        if f'isa{k}' not in df: df[f'isa{k}'] = np.nan
        if f'hi{k}' not in df: df[f'hi{k}'] = np.nan
        df[f'D{k}'] = df[f'isa{k}'] * 10
    df['Dwc'] = df.wc_built * 10; df['Dnb'] = df.nb1k_isa * 10
    folds = E.folds_by_block(df.blk2.values); R = dict(city=c)
    ok = lambda cols: df[cols].notna().all(1)
    # (a) lagged outcome
    for nm, m in [('lag_unsealed', ok(['hi3', 'hi0', 'Dwc', 'D0'] + WL) & (df.isa0 < 0.05)), ('lag_all', ok(['hi3', 'hi0', 'Dwc', 'D0'] + WL))]:
        if m.sum() > 2000 and df.loc[m, 'Dwc'].std() > 0.2:
            dd = df[m].reset_index(drop=True); o = E.dml(dd, 'hi3', 'Dwc', WL + ['hi0', 'D0'], cat=['bin5'], folds=folds[m.values])
            o2 = E.dml(dd, 'hi3', 'Dwc', WL, cat=['bin5'], folds=folds[m.values])
            R.update({f'{nm}_theta': o['theta'], f'{nm}_se': o['se'], f'{nm}_ref_theta': o2['theta'], f'{nm}_ref_se': o2['se'], f'{nm}_n': int(m.sum())})
    # (b) spillover
    m = ok(['hi3', 'Dwc', 'Dnb'] + WL)
    dd = df[m].reset_index(drop=True); fd = folds[m.values]
    Yt = E.resid(dd.hi3.values, dd[WL], fd, ['bin5']); D1 = E.resid(dd.Dwc.values, dd[WL], fd, ['bin5']); D2 = E.resid(dd.Dnb.values, dd[WL], fd, ['bin5'])
    b, se, _ = E.ols_cluster(Yt, np.column_stack([D1, D2]), dd.blk2.values)
    R.update(sp_own=b[0], sp_own_se=se[0], sp_nb=b[1], sp_nb_se=se[1], sp_corr=float(np.corrcoef(D1, D2)[0, 1]))
    # (c) inner region
    m = ok(['hi3', 'Dwc'] + WL) & (df.rdist <= 0.5)
    if m.sum() > 2000:
        dd = df[m].reset_index(drop=True); o = E.dml(dd, 'hi3', 'Dwc', WL, cat=['bin5'], folds=folds[m.values])
        R.update(inner_theta=o['theta'], inner_se=o['se'], inner_n=int(m.sum()))
    # (d) concordant dating
    if 'cci_urban_1992' in df:
        designs = [('cA', (df.isa0 < 0.1) & (df.isa1 < 0.1) & (df.cci_urban_1992 < 0.05) & (df.cci_urban_2000 < 0.05), df.D2 - df.D1, df.cci_urban_2014 - df.cci_urban_2000, {'pre1': (0, 1), 'post': (1, 2), 'post2': (2, 3)}),
                   ('cB', (df.isa0 < 0.1) & (df.isa1 < 0.1) & (df.isa2 < 0.1) & (df.cci_urban_2014 < 0.05), df.D3 - df.D2, df.cci_urban_2020 - df.cci_urban_2014, {'pre2': (0, 1), 'pre1': (1, 2), 'post': (2, 3)})]
        for nm, base, bdose, cdose, per in designs:
            tr = base & (bdose >= 1) & (cdose >= 0.2); co = base & (bdose < 0.5) & (cdose < 0.05)
            R[f'{nm}_ntreated'] = int(tr.sum())
            if tr.sum() < 30 or co.sum() < 1000: continue
            df['dose'] = np.where(tr, bdose, 0.0)
            mk = (tr | co) & ok([f'hi{k}' for k in range(4)] + WL)
            dk = df[mk].reset_index(drop=True); fk = folds[mk.values]
            Dt = E.resid(dk.dose.values, dk[WL], fk, ['bin5'])
            for pn, (a_, b_) in per.items():
                dk['dY'] = dk[f'hi{b_}'] - dk[f'hi{a_}']
                try:
                    o = E.dml(dk, 'dY', 'dose', WL, cat=['bin5'], folds=fk, Dt_given=Dt)
                    R.update({f'{nm}_{pn}_theta': o['theta'], f'{nm}_{pn}_se': o['se']})
                except np.linalg.LinAlgError: pass
    # (e) calibration slope of WorldCover on out-of-fold back-cast (2021-2025)
    m = ok(['wc_built', 'isa3'])
    x, y = df.loc[m, 'isa3'].values, df.loc[m, 'wc_built'].values
    R['cal_slope'] = float(np.cov(x, y)[0, 1] / np.var(x)); R['cal_sd_ratio'] = float(np.std(x) / np.std(y))
    R['runtime_s'] = round(time.time() - t0, 1)
    json.dump({k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in R.items()}, open(fo, 'w'))
    return R['runtime_s']


if __name__ == '__main__':
    part, n = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    for c in list(cities().city)[part::n]:
        try: print(c, run(c), flush=True)
        except Exception as ex:
            import traceback; traceback.print_exc(); print('FAILED', c, flush=True)
