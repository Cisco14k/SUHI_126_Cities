"""LCMAP CONUS v1.3 primary land cover: developed fraction (class 1) on the 120 m grid of the US city-regions,
for 1987, 2000, 2014 and 2021 (mid-points of the epochs; LCMAP ends in 2021). Independent of the back-cast."""
import sys, os, numpy as np, rasterio, pystac_client, planetary_computer as pc
from rasterio.warp import transform_bounds
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from static126 import read_mosaic, to_grid
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
YEARS = (1987, 2000, 2014, 2021)
US = ['Bakersfield', 'Denver', 'Louisville', 'Memphis', 'Milwaukee', 'Omaha', 'Pittsburgh', 'Raleigh', 'Reno', 'Tucson', 'Virginia Beach', 'Washington DC']
os.makedirs(f'{DATA}/lcmap', exist_ok=True)
cs = cities()
for _, c in cs[cs.city.isin(US)].iterrows():
    out = f'{DATA}/lcmap/{slug(c.city)}.npz'
    if os.path.exists(out): continue
    g = city_grid(c); n = g['shape'][0]; b = rasterio.transform.array_bounds(n, n, g['transform'])
    b4 = transform_bounds(g['epsg'], 4326, *b, densify_pts=21)
    res = {}
    for yr in YEARS:
        its = list(cat.search(collections=['usgs-lcmap-conus-v13'], bbox=list(b4), datetime=f'{yr}-01-01/{yr}-12-31').items())
        with rasterio.open(its[0].assets['lcpri'].href) as s0: crs = s0.crs
        bs = transform_bounds(4326, crs, *b4, densify_pts=21)
        a, tr, crs = read_mosaic(its, 'lcpri', bs)
        res[f'dev{yr}'] = to_grid(a == 1, tr, crs, g)
    np.savez_compressed(out, **res); print(c.city, flush=True)
