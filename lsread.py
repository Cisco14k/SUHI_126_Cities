"""Landsat C2 L2 scene reading on a city grid (from the earlier pipeline): QA masking, OLI harmonization, sampling."""
import os, numpy as np, rasterio, planetary_computer as pc
from rasterio.windows import from_bounds
SR_BANDS = ['blue', 'green', 'red', 'nir08', 'swir16', 'swir22']
# Roy et al. (2016) ETM+/TM -> OLI OLS harmonization (slope, intercept) for surface reflectance
ROY = {'blue': (0.8474, 0.0003), 'green': (0.8483, 0.0088), 'red': (0.9047, 0.0061),
       'nir08': (0.8462, 0.0412), 'swir16': (0.8937, 0.0254), 'swir22': (0.9071, 0.0172)}
os.environ.setdefault('GDAL_CACHEMAX', '128'); os.environ.setdefault('GDAL_HTTP_MERGE_CONSECUTIVE_RANGES', 'YES'); os.environ.setdefault('GDAL_HTTP_MULTIPLEX', 'YES'); os.environ.setdefault('GDAL_HTTP_VERSION', '2'); os.environ.setdefault('GDAL_HTTP_MAX_RETRY', '5'); os.environ.setdefault('GDAL_HTTP_RETRY_DELAY', '2')
os.environ.setdefault('GDAL_DISABLE_READDIR_ON_OPEN', 'EMPTY_DIR'); os.environ.setdefault('CPL_VSIL_CURL_ALLOWED_EXTENSIONS', '.tif')


from scipy.ndimage import map_coordinates, binary_dilation
from pyproj import Transformer
_COORD = {}


def scene_coords(g, epsg, key):
    """City-grid cell centres expressed in a scene CRS (cached per city and CRS)."""
    k = (key, epsg)
    if k not in _COORD:
        if epsg == g['epsg']:
            _COORD[k] = (g['X'], g['Y'])
        else:
            tr = Transformer.from_crs(g['epsg'], epsg, always_xy=True)
            _COORD[k] = tr.transform(g['X'], g['Y'])
    return _COORD[k]


def read_band(href, b_scene, overview=1):
    href = pc.sign(href)
    with rasterio.open(href, overview_level=overview) as ds:
        w = from_bounds(*b_scene, ds.transform).round_offsets().round_lengths()
        a = ds.read(1, window=w, boundless=True, fill_value=0)
        wt = ds.window_transform(w)
    return a, wt


def sample(a, wt, XY, order):
    inv = ~wt
    col, row = inv * (XY[0], XY[1])
    return map_coordinates(a, [row - 0.5, col - 0.5], order=order, mode='constant', cval=np.nan if a.dtype.kind == 'f' else 0, prefilter=False)


def process_scene(sc, g, b_scene, XY, read_sr=True):
    """Returns dict with lst (degC), clear mask and OLI-harmonized SR bands on the city grid, or ok=False."""
    q, qt = read_band(sc['assets']['qa_pixel'], b_scene)
    q = q.astype(np.uint16)
    fill = (q & 1) > 0
    bad = ((q >> 1) & 1) | ((q >> 3) & 1) | ((q >> 4) & 1) | ((q >> 5) & 1)
    if sc['platform'] in ('landsat-8', 'landsat-9'):
        bad = bad | ((q >> 2) & 1)
    bad = binary_dilation(bad.astype(bool) | (q == 0), iterations=1)      # one-cell buffer around clouds, shadows and gaps
    clear_src = (~bad & ~fill).astype(np.uint8)
    valid_src = (~fill & (q > 0)).astype(np.uint8)
    cf = sample(clear_src, qt, XY, 0) > 0
    vf = sample(valid_src, qt, XY, 0) > 0
    inside = g['dist'] <= g['R']
    nin = (inside & vf).sum()
    cover = float(nin / inside.sum())
    clear_share = float((cf & inside).sum() / max(nin, 1))
    if clear_share < 0.2 or cover < 0.5:
        return dict(ok=False, clear_share=clear_share, cover=cover)
    th = 'lwir11' if 'lwir11' in sc['assets'] else 'lwir'
    out = dict(ok=True, clear_share=clear_share, cover=cover)
    a, wt = read_band(sc['assets'][th], b_scene)
    a = a.astype(np.float32); a[a == 0] = np.nan
    d = sample(a * 0.00341802 + 149.0 - 273.15, wt, XY, 1).astype(np.float32)
    d[~cf] = np.nan
    out['lst'] = d
    out['sr'] = read_sr
    if not read_sr: return out
    harm = sc['platform'] in ('landsat-4', 'landsat-5', 'landsat-7')
    for b in SR_BANDS:
        a, wt = read_band(sc['assets'][b], b_scene)
        a = a.astype(np.float32); a[a == 0] = np.nan
        a = a * 2.75e-5 - 0.2
        if harm:
            s_, i_ = ROY[b]; a = s_ * a + i_
        d = sample(a, wt, XY, 1).astype(np.float32)
        d[~cf] = np.nan
        out[b] = np.clip(d, -0.05, 1.2)
    return out


def nanq(st, qs):
    """Fast NaN-aware quantiles along axis 0 (lower-median convention via linear interpolation of the sorted valid values)."""
    srt = np.sort(st, axis=0)                      # NaNs sort to the end
    n = np.isfinite(srt).sum(0)
    out = []
    for q in qs:
        pos = np.clip(q * (n - 1), 0, None); lo = np.floor(pos).astype(int); hi = np.minimum(lo + 1, np.maximum(n - 1, 0))
        fr = pos - lo
        a = np.take_along_axis(srt, lo[None], 0)[0]; b = np.take_along_axis(srt, hi[None], 0)[0]
        v = a + (b - a) * fr
        v[n == 0] = np.nan
        out.append(v.astype(np.float32))
    return out


