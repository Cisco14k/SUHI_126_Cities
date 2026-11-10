"""Round 4: spillover and total effect with finer location control (2-km location bins instead of 5-km),
to test whether the neighbourhood effect reflects neighbourhood-scale confounding."""
import sys, os, json, time, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
OUT = f'{RES}/city_extra2'; os.makedirs(OUT, exist_ok=True)


def run(c):
    s = slug(c); fo = f'{OUT}/{s}.json'
    if os.path.exists(fo): return 'skip'
    h = pd.read_parquet(f'{DATA}/hi/{s}.parquet')
    d = pd.read_parquet(f'{DATA}/cells2/{s}.parquet')[['cell', 'bin5', 'blk2']]
    df = h.merge(d, on='cell', how='left'); df['Dwc'] = df.wc_built * 10; df['Dnb'] = df.nb1k_isa * 10
    df['bin2'] = df['blk2']  # 2-km blocks as location bins
    W2 = E.TERRAIN + ['bin2']
    m = df[['hi3', 'Dwc', 'Dnb'] + W2].notna().all(1); dd = df[m].reset_index(drop=True)
    fd = E.folds_by_block((np.floor(dd.dx / 4) * 1000 + np.floor(dd.dy / 4)).values)  # 4-km folds so bins appear in training folds
    Yt = E.resid(dd.hi3.values, dd[W2], fd, ['bin2']); D1 = E.resid(dd.Dwc.values, dd[W2], fd, ['bin2']); D2 = E.resid(dd.Dnb.values, dd[W2], fd, ['bin2'])
    b, se, _ = E.ols_cluster(Yt, np.column_stack([D1, D2]), dd.blk2.values)
    b1, se1, _ = E.ols_cluster(Yt, D1, dd.blk2.values)
    R = dict(city=c, sp2_own=b[0], sp2_own_se=se[0], sp2_nb=b[1], sp2_nb_se=se[1], tot2=b1[0], tot2_se=se1[0], n=int(m.sum()))
    json.dump({k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in R.items()}, open(fo, 'w')); return 'ok'


if __name__ == '__main__':
    part, n = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    for c in list(cities().city)[part::n]:
        try: print(c, run(c), flush=True)
        except Exception as ex: print('FAILED', c, ex, flush=True)
