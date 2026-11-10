"""Round 5: (a) concordant dating with ESA CCI change as the dose (independent of the Landsat back-cast);
(b) lagged-outcome adjustment restricted to cells still vegetated in 1985-1989 (NDVI above the city's rural median),
where pre-sealing clearing cannot already be in the 1985-1989 heat island."""
import sys, os, json, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
WL = E.TERRAIN + E.LOC; OUT = f'{RES}/city_extra3'; os.makedirs(OUT, exist_ok=True)


def run(c):
    s = slug(c); fo = f'{OUT}/{s}.json'
    if os.path.exists(fo): return 'skip'
    h = pd.read_parquet(f'{DATA}/hi/{s}.parquet'); d = pd.read_parquet(f'{DATA}/cells2/{s}.parquet')
    d = d[[x for x in ['cell', 'bin5', 'blk2', 'cci_urban_1992', 'cci_urban_2000', 'cci_urban_2014', 'cci_urban_2020'] if x in d]]
    df = h.merge(d, on='cell', how='left'); folds = E.folds_by_block(df.blk2.values); R = dict(city=c)
    for k in range(4): df[f'D{k}'] = df[f'isa{k}'] * 10
    df['Dwc'] = df.wc_built * 10
    ok = lambda cols: df[cols].notna().all(1)
    if 'cci_urban_1992' in df:
        base = (df.isa0 < 0.1) & (df.isa1 < 0.1) & (df.cci_urban_1992 < 0.05) & (df.cci_urban_2000 < 0.05)
        bd, cd = df.D2 - df.D1, df.cci_urban_2014 - df.cci_urban_2000
        tr = base & (bd >= 1) & (cd >= 0.2); co = base & (bd < 0.5) & (cd < 0.05); R['ntr'] = int(tr.sum())
        if tr.sum() >= 30 and co.sum() >= 1000:
            df['dose'] = np.where(tr, cd * 10, 0.0)
            mk = (tr | co) & ok(['hi0', 'hi1', 'hi2'] + WL); dk = df[mk].reset_index(drop=True); fk = folds[mk.values]
            Dt = E.resid(dk.dose.values, dk[WL], fk, ['bin5'])
            for pn, (a_, b_) in {'pre1': (0, 1), 'post': (1, 2)}.items():
                dk['dY'] = dk[f'hi{b_}'] - dk[f'hi{a_}']
                o = E.dml(dk, 'dY', 'dose', WL, cat=['bin5'], folds=fk, Dt_given=Dt); R[f'cc_{pn}'] = o['theta']; R[f'cc_{pn}_se'] = o['se']
    # (b) lagged outcome in cells vegetated in 1985-1989
    rur = (df.nb1k_isa < 0.05)
    thr = np.nanmedian(df.loc[rur, 'ndvi0']) if rur.sum() > 100 else np.nanmedian(df.ndvi0)
    m = ok(['hi3', 'hi0', 'Dwc', 'D0'] + WL) & (df.isa0 < 0.05) & (df.ndvi0 >= thr)
    if m.sum() > 2000 and df.loc[m, 'Dwc'].std() > 0.2:
        dd = df[m].reset_index(drop=True)
        o = E.dml(dd, 'hi3', 'Dwc', WL + ['hi0', 'D0'], cat=['bin5'], folds=folds[m.values]); o2 = E.dml(dd, 'hi3', 'Dwc', WL, cat=['bin5'], folds=folds[m.values])
        R.update(lagveg=o['theta'], lagveg_se=o['se'], lagveg_ref=o2['theta'], lagveg_ref_se=o2['se'], lagveg_n=int(m.sum()))
    json.dump({k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in R.items()}, open(fo, 'w')); return 'ok'


if __name__ == '__main__':
    part, n = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    for c in list(cities().city)[part::n]:
        try: print(c, run(c), flush=True)
        except Exception as ex: print('FAILED', c, ex, flush=True)
