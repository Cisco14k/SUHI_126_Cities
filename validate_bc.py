"""Temporal validation of the back-cast impervious cover against products independent of it, at 1.2-km blocks:
ESA CCI land cover urban fraction (300 m; 1992, 2000, 2014, 2020; global) and LCMAP developed fraction (30 m;
1987, 2000, 2014, 2021; 12 US city-regions). Reports level and change agreement (Pearson r of block means)."""
import sys, os, glob, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
PAIRS_CCI = {(1, 3): ('cci_urban_2000', 'cci_urban_2020'), (2, 3): ('cci_urban_2014', 'cci_urban_2020'), (0, 3): ('cci_urban_1992', 'cci_urban_2020'), (0, 1): ('cci_urban_1992', 'cci_urban_2000')}
LEV_CCI = {0: 'cci_urban_1992', 1: 'cci_urban_2000', 2: 'cci_urban_2014', 3: 'cci_urban_2020'}
LEV_LC = {0: 'dev1987', 1: 'dev2000', 2: 'dev2014', 3: 'dev2021'}
rows = []
for f in sorted(glob.glob(f'{DATA}/cells2/*.parquet')):
    d = pd.read_parquet(f); c = d.city.iloc[0]
    d['b'] = (np.floor(d.dx / 1.2) * 1000 + np.floor(d.dy / 1.2)).astype(int)
    fl = f'{DATA}/lcmap/{slug(c)}.npz'
    if os.path.exists(fl):
        L = np.load(fl)
        for k, v in LEV_LC.items(): d[v] = L[v].ravel()[d.cell.values]
    agg = {**{f'isa{k}': 'mean' for k in range(4)}, **{v: 'mean' for v in LEV_CCI.values() if v in d}, 'wc_built': 'mean', 'cell': 'size'}
    if os.path.exists(fl): agg.update({v: 'mean' for v in LEV_LC.values()})
    B = d.groupby('b').agg(agg); B = B[B.cell >= 8]
    r = dict(city=c, nblocks=len(B))
    for k, v in LEV_CCI.items():
        if v in B: r[f'cci_lev{k}'] = B[f'isa{k}'].corr(B[v])
    for (a, b), (va, vb) in PAIRS_CCI.items():
        if va in B and vb in B:
            x = B[f'isa{b}'] - B[f'isa{a}']; y = B[vb] - B[va]
            r[f'cci_chg{a}{b}'] = x.corr(y) if y.std() > 0 else np.nan
            r[f'cci_chg{a}{b}_mean_bc'] = x.mean(); r[f'cci_chg{a}{b}_mean_cci'] = y.mean()
    if os.path.exists(fl):
        for k, v in LEV_LC.items(): r[f'lc_lev{k}'] = B[f'isa{k}'].corr(B[v]); r[f'lc_mean{k}_bc'] = B[f'isa{k}'].mean(); r[f'lc_mean{k}'] = B[v].mean()
        for a, b in [(0, 3), (1, 3), (0, 1), (2, 3)]:
            x = B[f'isa{b}'] - B[f'isa{a}']; y = B[LEV_LC[b]] - B[LEV_LC[a]]; r[f'lc_chg{a}{b}'] = x.corr(y)
    rows.append(r)
R = pd.DataFrame(rows); R.to_csv(f'{RES}/backcast_temporal.csv', index=False)
print(R.drop(columns='city').median().round(3).to_string())
