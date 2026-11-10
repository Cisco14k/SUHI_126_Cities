"""Back-cast impervious (ISA) and tree cover to 1985-1989, 1998-2002 and 2012-2016 with a pooled LightGBM
trained on 2021-2025 Landsat composites against ESA WorldCover 2021 (120 m fractions).
Features: OLI-harmonized surface reflectance, spectral indices and albedo, each also expressed relative to the
city-epoch median (removes residual cross-sensor and phenology offsets).
Validation: (i) city-grouped five-fold CV R2 in 2021-2025; (ii) temporal agreement of 1.2-km block changes with
ESA CCI urban fraction (2000->2020, 2014->2020, 1992->2020) globally; (iii) LCMAP developed fraction (US cities)."""
import sys, os, glob, numpy as np, pandas as pd, lightgbm as lgb, json
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
SPEC = ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22', 'ndvi20', 'ndvi', 'ndvi80', 'mndwi', 'ndbi', 'albedo']
P = dict(objective='regression', learning_rate=0.05, num_leaves=63, min_data_in_leaf=50, feature_fraction=0.8,
         bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, verbose=-1, num_threads=1)
NR = 300


def feats(df, k):
    F = pd.DataFrame({s: df[f'{s}{k}'].values for s in SPEC})
    med = F.median()
    for s in SPEC: F[s + '_rel'] = F[s] - med[s]
    return F


def load():
    fs = sorted(glob.glob(f'{DATA}/cells/*.parquet'))
    return pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)


def city_model(d, seed=0):
    """City-specific back-cast: LightGBM trained on the city's own 2021-2025 composite against WorldCover 2021,
    2-km spatial-block five-fold CV (out-of-fold predictions are used for 2021-2025 so that all epochs are
    predictions of the same kind), final model applied to the earlier epochs."""
    ok3 = np.isfinite(d['ndvi3'].values)
    X3 = feats(d, 3); blk = d['blk2'].values
    ub = np.unique(blk); rng = np.random.default_rng(seed); fmap = dict(zip(ub, rng.permutation(len(ub)) % 5)); fv = np.array([fmap[b] for b in blk])
    out, cv = {}, {}
    for tgt, nm in [('wc_built', 'isa'), ('wc_tree', 'tree')]:
        y = d[tgt].values; oof = np.full(len(d), np.nan)
        for f in range(5):
            tr, te = ok3 & (fv != f), ok3 & (fv == f)
            if te.sum() == 0: continue
            m = lgb.train(P, lgb.Dataset(X3[tr], y[tr]), NR); oof[te] = m.predict(X3[te])
        oof = np.clip(oof, 0, 1); yy, pp = y[ok3], oof[ok3]
        cv[f'{nm}_r2'] = 1 - ((yy - pp) ** 2).sum() / ((yy - yy.mean()) ** 2).sum(); cv[f'{nm}_mae'] = float(np.abs(yy - pp).mean())
        cv[f'{nm}_bias'] = float((pp - yy).mean())
        m = lgb.train(P, lgb.Dataset(X3[ok3], y[ok3]), NR)
        out[f'{nm}3'] = oof.astype(np.float32)
        for k in range(3):
            if f'ndvi{k}' not in d or d[f'ndvi{k}'].isna().all(): out[f'{nm}{k}'] = np.full(len(d), np.nan, np.float32); continue
            ok = np.isfinite(d[f'ndvi{k}'].values); p = np.full(len(d), np.nan); p[ok] = np.clip(m.predict(feats(d, k)[ok]), 0, 1)
            out[f'{nm}{k}'] = p.astype(np.float32)
    return out, cv


if __name__ == '__main__':
    import glob as _g
    os.makedirs(f'{DATA}/cells2', exist_ok=True); rows = []
    for f in sorted(_g.glob(f'{DATA}/cells/*.parquet')):
        o = f.replace('/cells/', '/cells2/')
        d = pd.read_parquet(f)
        if os.path.exists(o) and os.path.getmtime(o) > os.path.getmtime(f):
            continue
        out, cv = city_model(d)
        for k, v in out.items(): d[k] = v
        d.to_parquet(o, index=False); cv['city'] = d.city.iloc[0]; rows.append(cv); print(cv, flush=True)
    fn = f'{RES}/backcast_cv.csv'
    old = pd.read_csv(fn) if os.path.exists(fn) else pd.DataFrame()
    if len(old) and 'isa_r2' in old: old = old[~old.city.isin([r['city'] for r in rows])]
    else: old = pd.DataFrame()
    pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(fn, index=False)
