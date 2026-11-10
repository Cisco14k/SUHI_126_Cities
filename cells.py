"""Per city: sample up to NS land cells inside the city-region circle and assemble a cell table with
Landsat composites (4 epochs), WorldCover 2021 fractions, terrain, population, ESA CCI urban fractions,
distance to water, 1-km neighbourhood impervious cover (strata), location bins and offsets."""
import sys, os, numpy as np, pandas as pd, time
from scipy.ndimage import distance_transform_edt, uniform_filter
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
NS = 30000
SPEC = ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22', 'ndvi20', 'ndvi', 'ndvi80', 'mndwi', 'ndbi', 'albedo']


def do_city(c, seed=0):
    out = f'{DATA}/cells/{slug(c.city)}.parquet'
    if os.path.exists(out): return 'skip'
    fl, fs = f'{DATA}/landsat/{slug(c.city)}.npz', f'{DATA}/static/{slug(c.city)}.npz'
    if not (os.path.exists(fl) and os.path.exists(fs)): return 'missing'
    g = city_grid(c); L = np.load(fl); S = np.load(fs)
    water = np.nan_to_num(S['wc_water'], nan=0) >= 0.5
    dwat = distance_transform_edt(~water) * CELL / 1000.0
    built = np.nan_to_num(S['wc_built'], nan=0)
    nb1k = uniform_filter(built, 9)
    land = (g['dist'] <= g['R']) & ~water & np.isfinite(S['elev']) & np.isfinite(S['wc_built'])
    idx = np.flatnonzero(land.ravel())
    rng = np.random.default_rng(seed)
    if len(idx) > NS: idx = np.sort(rng.choice(idx, NS, replace=False))
    d = {'cell': idx.astype(np.int32)}
    X = g['X'].ravel()[idx] - g['x0']; Y = g['Y'].ravel()[idx] - g['y0']
    d['dx'] = (X / 1000).astype(np.float32); d['dy'] = (Y / 1000).astype(np.float32)
    d['dist'] = (np.hypot(X, Y) / 1000).astype(np.float32); d['rdist'] = (d['dist'] / (g['R'] / 1000)).astype(np.float32)
    d['bin5'] = ((np.floor(X / 5000) + 20) * 100 + (np.floor(Y / 5000) + 20)).astype(np.int32)
    d['blk2'] = ((np.floor(X / 2000) + 50) * 1000 + (np.floor(Y / 2000) + 50)).astype(np.int32)
    for k in ['wc_tree', 'wc_grass', 'wc_bare', 'wc_built', 'wc_water', 'elev', 'slope', 'aspect_sin', 'aspect_cos', 'elev_sd', 'pop2020',
              'cci_urban_1992', 'cci_urban_2000', 'cci_urban_2014', 'cci_urban_2020']:
        if k in S: d[k] = S[k].ravel()[idx].astype(np.float32)
    d['dwater'] = np.minimum(dwat.ravel()[idx], 20).astype(np.float32)
    d['nb1k_isa'] = nb1k.ravel()[idx].astype(np.float32)
    for k in range(4):
        if f'e{k}_lst' not in L: continue
        d[f'lst{k}'] = L[f'e{k}_lst'].ravel()[idx].astype(np.float32)
        d[f'nobs{k}'] = L[f'e{k}_nobs'].ravel()[idx].astype(np.int16)
        for s in SPEC: d[f'{s}{k}'] = L[f'e{k}_{s}'].ravel()[idx].astype(np.float32)
    df = pd.DataFrame(d); df.insert(0, 'city', c.city)
    os.makedirs(f'{DATA}/cells', exist_ok=True); df.to_parquet(out, index=False)
    return len(df)


if __name__ == '__main__':
    cs = cities(); sel = sys.argv[1:] or list(cs.city)
    for _, c in cs[cs.city.isin(sel)].iterrows():
        t = time.time()
        try: r = do_city(c)
        except Exception as e: r = f'ERR {e!r}'[:120]
        print(c.city, r, round(time.time() - t, 1), flush=True)
