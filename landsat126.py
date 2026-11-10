"""Per city and epoch: warm-season median composites of Landsat Collection 2 Level-2 surface temperature and surface
reflectance on the 120 m city grid (observed values only; no gap filling).

Epochs: 1985-1989, 1998-2002, 2012-2016, 2021-2025. Warm season: the three months with the highest 1991-2020 mean
TerraClimate maximum temperature. Up to 16 scenes per epoch (cloud cover < 70%, at most 4 per year, least cloudy first);
Landsat 7 scenes after 2016 are excluded because of its orbit drift (later overpass times). TM and ETM+ reflectance are
harmonized to OLI (Roy et al. 2016)."""
import sys, os, json, time, numpy as np, pandas as pd, rasterio, pystac_client, planetary_computer as pc, pickle
from rasterio.warp import transform_bounds
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, '/home/claude/w126/scripts')
import lsread as L          # read_band, sample, process_scene, nanq, scene_coords
from common import *

MAXS = 16; PER_YEAR = 4
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")


def warm_months(city):
    tc = pickle.load(open(f'{DATA}/terraclimate.pkl', 'rb'))[city]['tmax']
    s = tc.mean(['lat', 'lon']).to_series(); s = s['1991':'2020']
    clim = s.groupby(s.index.month).mean()
    return sorted(clim.sort_values(ascending=False).index[:3].tolist())


def search(c, months, y0, y1):
    pt = {'type': 'Point', 'coordinates': [float(c.lon), float(c.lat)]}
    items = []
    for it in cat.search(collections=['landsat-c2-l2'], intersects=pt, datetime=f'{y0}-01-01/{y1}-12-31',
                         query={'eo:cloud_cover': {'lt': 70}}).items():
        dt = pd.Timestamp(it.properties['datetime'])
        if dt.month not in months: continue
        pf = it.properties['platform']
        if pf == 'landsat-7' and dt.year > 2016: continue
        if 'lwir11' not in it.assets and 'lwir' not in it.assets: continue
        items.append(dict(id=it.id, datetime=it.properties['datetime'], platform=pf, cloud=it.properties['eo:cloud_cover'],
                          sun_el=it.properties.get('view:sun_elevation'), epsg=it.properties.get('proj:epsg') or it.properties.get('proj:code'),
                          assets={k: v.href for k, v in it.assets.items()}))
    items = sorted(items, key=lambda x: x['cloud']); sel, per = [], {}
    for x in items:
        y = int(x['datetime'][:4])
        if per.get(y, 0) >= PER_YEAR: continue
        sel.append(x); per[y] = per.get(y, 0) + 1
        if len(sel) >= MAXS: break
    return sel


def do_city(c, nthreads=10):
    out = f'{DATA}/landsat/{slug(c.city)}.npz'
    if os.path.exists(out): return
    g = city_grid(c); n = g['shape'][0]
    b = rasterio.transform.array_bounds(n, n, g['transform'])
    months = warm_months(c.city); res = {}; meta = []
    for k, (y0, y1) in enumerate(EPOCHS):
        scenes = search(c, months, y0, y1)
        def job(sc):
            epsg = int(str(sc['epsg']).split(':')[-1])
            bs = transform_bounds(g['epsg'], epsg, *b, densify_pts=21); bs = (bs[0] - 500, bs[1] - 500, bs[2] + 500, bs[3] + 500)
            XY = L.scene_coords(g, epsg, c.city)
            for a in range(3):
                try: return L.process_scene(sc, g, bs, XY, True)
                except Exception as e: err = repr(e); time.sleep(3)
            return dict(ok=False, error=err)
        with ThreadPoolExecutor(nthreads) as ex: outs = list(ex.map(job, scenes))
        good = [(sc, o) for sc, o in zip(scenes, outs) if o.get('ok')]
        for sc, o in zip(scenes, outs):
            meta.append(dict(epoch=k, id=sc['id'], datetime=sc['datetime'], platform=sc['platform'], cloud=sc['cloud'], sun_el=sc['sun_el'],
                             ok=bool(o.get('ok')), clear_share=o.get('clear_share'), cover=o.get('cover'), error=o.get('error')))
        if len(good) < 2: continue
        lst = np.stack([o['lst'] for _, o in good]).astype(np.float32)
        res[f'e{k}_lst'] = np.nanmedian(lst, 0).astype(np.float32); res[f'e{k}_nobs'] = np.isfinite(lst).sum(0).astype(np.int16)
        res[f'e{k}_lst_iqr'] = (np.nanpercentile(lst, 75, 0) - np.nanpercentile(lst, 25, 0)).astype(np.float16)
        del lst
        B = {bb: np.stack([o[bb] for _, o in good]).astype(np.float32) for bb in L.SR_BANDS}
        ndvi = (B['nir08'] - B['red']) / (B['nir08'] + B['red'] + 1e-6)
        mndwi = (B['green'] - B['swir16']) / (B['green'] + B['swir16'] + 1e-6)
        ndbi = (B['swir16'] - B['nir08']) / (B['swir16'] + B['nir08'] + 1e-6)
        q = L.nanq(ndvi, [0.2, 0.5, 0.8]); res[f'e{k}_ndvi20'], res[f'e{k}_ndvi'], res[f'e{k}_ndvi80'] = [x.astype(np.float16) for x in q]
        res[f'e{k}_mndwi'] = np.nanmedian(mndwi, 0).astype(np.float16); res[f'e{k}_ndbi'] = np.nanmedian(ndbi, 0).astype(np.float16)
        med = {bb: np.nanmedian(B[bb], 0).astype(np.float32) for bb in L.SR_BANDS}
        for bb in L.SR_BANDS: res[f'e{k}_{bb}'] = med[bb].astype(np.float16)
        # broadband albedo (Liang 2001, Landsat shortwave)
        res[f'e{k}_albedo'] = (0.356 * med['blue'] + 0.130 * med['red'] + 0.373 * med['nir08'] + 0.085 * med['swir16'] + 0.072 * med['swir22'] - 0.0018).astype(np.float32)
        res[f'e{k}_nscene'] = np.int16(len(good))
        del B, ndvi, mndwi, ndbi
    os.makedirs(f'{DATA}/landsat', exist_ok=True)
    np.savez_compressed(out, **res)
    pd.DataFrame(meta).to_csv(out.replace('.npz', '_scenes.csv'), index=False)
    json.dump(dict(months=months), open(out.replace('.npz', '_meta.json'), 'w'))


if __name__ == '__main__':
    cs = cities(); sel = (open(sys.argv[1][1:]).read().split('\n') if sys.argv[1:] and sys.argv[1].startswith('@') else sys.argv[1:]) or list(cs.city)
    for _, c in cs[cs.city.isin(sel)].iterrows():
        t = time.time()
        try: do_city(c)
        except Exception as e:
            import traceback; traceback.print_exc(); print('FAILED', c.city, flush=True); continue
        print(c.city, round(time.time() - t), flush=True)
