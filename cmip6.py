"""Extract NEX-GDDP-CMIP6 daily tasmax/pr at the 126 city points (3x3 cell mean around the
nearest 0.25 deg cell), sampling every 4th day, for a 5-model ISIMIP3b ensemble.
Baseline: historical 1995-2014 (every 2nd year); futures: 2041-2070 and 2071-2100 (every 3rd year)
under SSP2-4.5 and SSP5-8.5.  Output: data/cmip6/{model}_{scen}_{year}_{var}.npz with monthly
means per city (12 x 126) -- tasmax in degC, pr in mm/day."""
import sys, os, zlib, time, json, numpy as np, pandas as pd, requests, fsspec, h5py
from concurrent.futures import ThreadPoolExecutor
import pystac_client, planetary_computer as pc
ROOT = '/home/claude/w126'; OUT = f'{ROOT}/data/cmip6'; os.makedirs(OUT, exist_ok=True)
MODELS = ['GFDL-ESM4', 'IPSL-CM6A-LR', 'MPI-ESM1-2-HR', 'MRI-ESM2-0', 'UKESM1-0-LL']
VARS = ['tasmax', 'pr']
JOBS = [('historical', y) for y in range(1995, 2015, 2)] + \
       [(s, y) for s in ('ssp245', 'ssp585') for y in list(range(2041, 2071, 3)) + list(range(2071, 2101, 3))]
cty = pd.read_csv(f'{ROOT}/data/cities.csv')
lat = -59.875 + 0.25 * np.arange(600); lon = 0.125 + 0.25 * np.arange(1440)
iy = np.clip(np.round((cty.lat.values + 59.875) / 0.25).astype(int), 1, 598)
ix = np.round(((cty.lon.values % 360) - 0.125) / 0.25).astype(int) % 1440
YY = iy[:, None, None] + np.array([-1, 0, 1])[None, :, None]
XX = (ix[:, None, None] + np.array([-1, 0, 1])[None, None, :]) % 1440
cat = pystac_client.Client.open('https://planetarycomputer.microsoft.com/api/stac/v1', modifier=pc.sign_inplace)
col = cat.get_collection('nasa-nex-gddp-cmip6')
S = requests.Session()

def unshuffle(b, n=4):
    a = np.frombuffer(b, np.uint8).reshape(n, -1)
    return a.T.copy().view('<f4').ravel()

def getrange(url, off, size):
    for k in range(5):
        try:
            r = S.get(url, headers={'Range': f'bytes={off}-{off+size-1}'}, timeout=60)
            if r.status_code in (200, 206) and len(r.content) == size:
                return r.content
        except Exception:
            pass
        time.sleep(2 + 3 * k)
    raise IOError('range failed')

def do(model, scen, year, var):
    fn = f'{OUT}/{model}_{scen}_{year}_{var}.npz'
    if os.path.exists(fn): return 'skip'
    it = col.get_item(f'{model}.{scen}.{year}')
    if it is None: return 'missing'
    url = it.assets[var].href
    with fsspec.open(url).open() as f:
        h = h5py.File(f); v = h[var]; nd = v.shape[0]
        days = list(range(1, nd, 4))
        info = [v.id.get_chunk_info_by_coord((d, 0, 0)) for d in days]
        shuffle = v.shuffle
    def one(ci):
        raw = zlib.decompress(getrange(url, ci.byte_offset, ci.size))
        a = (unshuffle(raw) if shuffle else np.frombuffer(raw, '<f4')).reshape(600, 1440)
        return np.nanmean(np.where(a[YY, XX] > 1e19, np.nan, a[YY, XX]), axis=(1, 2))
    with ThreadPoolExecutor(12) as ex:
        vals = np.array(list(ex.map(one, info)))          # nday x 126
    mon = np.minimum((np.array(days) * 12) // nd, 11)
    mm = np.array([np.nanmean(vals[mon == m], 0) for m in range(12)])
    mm = mm - 273.15 if var == 'tasmax' else mm * 86400.0
    np.savez_compressed(fn, mm=mm.astype('f4'), ndays=nd)
    return 'ok'

if __name__ == '__main__':
    part, nparts = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 1)
    tasks = [(m, s, y, v) for m in MODELS for (s, y) in JOBS for v in VARS][part::nparts]
    t0 = time.time()
    for i, t in enumerate(tasks):
        try:
            r = do(*t)
        except Exception as e:
            r = f'ERR {e}'
        print(i, len(tasks), *t, r, round(time.time() - t0), flush=True)
