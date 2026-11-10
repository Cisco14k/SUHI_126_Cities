"""Per city: ESA WorldCover 2021 class fractions, Copernicus DEM, GlobPOP 2020 counts and ESA CCI land-cover urban
fraction (1992, 2000, 2014, 2020; independent of Landsat back-casts) on the 120 m city grid."""
import sys, os, numpy as np, rasterio, pystac_client, planetary_computer as pc, time
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.windows import from_bounds
from rasterio.merge import merge
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *

cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
WC = {'tree': [10, 95], 'grass': [20, 30, 40, 90, 100], 'water': [80], 'bare': [60, 70], 'built': [50]}


def read_mosaic(items, asset, b):
    srcs = [rasterio.open(it.assets[asset].href) for it in items]
    arr, tr = merge(srcs, bounds=b); crs = srcs[0].crs
    for s in srcs: s.close()
    return arr[0], tr, crs


def to_grid(a, tr, crs, g, rs=Resampling.average, nod=None):
    d = np.full(g['shape'], np.nan, np.float32)
    reproject(a.astype(np.float32), d, src_transform=tr, src_crs=crs, dst_transform=g['transform'], dst_crs=g['epsg'], resampling=rs, src_nodata=nod, dst_nodata=np.nan)
    return d


def do_city(c):
    out = f'{DATA}/static/{slug(c.city)}.npz'
    if os.path.exists(out): return
    g = city_grid(c); n = g['shape'][0]
    b = rasterio.transform.array_bounds(n, n, g['transform'])
    b4 = transform_bounds(g['epsg'], 4326, *b, densify_pts=21); b4 = (b4[0] - 0.01, b4[1] - 0.01, b4[2] + 0.01, b4[3] + 0.01)
    res = {}
    items = [it for it in cat.search(collections=['esa-worldcover'], bbox=list(b4)).items() if '_2021_' in it.id]
    wc, tr, crs = read_mosaic(items, 'map', b4)
    val = to_grid((wc > 0), tr, crs, g)
    for k, codes in WC.items():
        d = to_grid(np.isin(wc, codes), tr, crs, g); res['wc_' + k] = np.where(val > 0.5, d / np.maximum(val, 1e-6), np.nan).astype(np.float32)
    del wc
    items = list(cat.search(collections=['cop-dem-glo-30'], bbox=list(b4)).items())
    dem, tr, crs = read_mosaic(items, 'data', b4)
    d = to_grid(dem, tr, crs, g, nod=-32767); res['elev'] = d
    gy, gx = np.gradient(np.nan_to_num(d, nan=np.nanmedian(d)), CELL)
    res['slope'] = np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32); asp = np.arctan2(-gx, gy)
    res['aspect_sin'] = np.sin(asp).astype(np.float32); res['aspect_cos'] = np.cos(asp).astype(np.float32)
    # elevation variability within 600 m
    from scipy.ndimage import generic_filter, uniform_filter
    e = np.nan_to_num(d, nan=np.nanmedian(d)); m1 = uniform_filter(e, 11); m2 = uniform_filter(e * e, 11)
    res['elev_sd'] = np.sqrt(np.maximum(m2 - m1 * m1, 0)).astype(np.float32)
    # GlobPOP 2020 (dasymetric later)
    with rasterio.open('/home/claude/work/data/pop/GlobPOP_Count_2020.tif') as ds:
        w = from_bounds(*b4, ds.transform).round_offsets().round_lengths(); a = ds.read(1, window=w).astype(np.float64); a[a < 0] = 0
        res['pop2020'] = to_grid(a / ((ds.res[0] * 111e3) ** 2 * abs(np.cos(np.radians(c.lat)))) * CELL ** 2, ds.window_transform(w), ds.crs, g, rs=Resampling.bilinear)
    # ESA CCI land cover, urban class (190), 300 m annual
    for yr in (1992, 2000, 2014, 2020):
        its = list(cat.search(collections=['esa-cci-lc'], bbox=list(b4), datetime=f'{yr}-01-01/{yr}-12-31').items())
        if not its: continue
        lc, tr, crs = read_mosaic(its, 'lccs_class', b4)
        res[f'cci_urban_{yr}'] = to_grid(lc == 190, tr, crs, g)
    np.savez_compressed(out, **res)


if __name__ == '__main__':
    os.makedirs(f'{DATA}/static', exist_ok=True)
    cs = cities(); sel = sys.argv[1:] or list(cs.city)
    for _, c in cs[cs.city.isin(sel)].iterrows():
        t = time.time()
        for a in range(3):
            try: do_city(c); break
            except Exception as e: print('retry', c.city, repr(e)[:200], flush=True); time.sleep(10)
        print(c.city, round(time.time() - t, 1), flush=True)
