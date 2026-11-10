"""Shared helpers: 126 city-regions, impervious cover and daytime land-surface temperature, 1985-2025."""
import numpy as np, pandas as pd, math, os
from pyproj import Transformer
from rasterio.transform import from_origin

ROOT = '/home/claude/w126'
DATA = f'{ROOT}/data'; RES = f'{ROOT}/results'; FIG = f'{ROOT}/figures'
CELL = 120.0
EPOCHS = [(1985, 1989), (1998, 2002), (2012, 2016), (2021, 2025)]
EP_LAB = ['1985–1989', '1998–2002', '2012–2016', '2021–2025']
EP_SHORT = ['1987', '2000', '2014', '2023']          # mid-years, used only in file keys


def cities():
    return pd.read_csv(f'{DATA}/cities.csv')


def slug(city):
    import unicodedata
    s = unicodedata.normalize('NFKD', city).encode('ascii', 'ignore').decode()
    return s.replace(' ', '_').replace("'", '').replace('.', '').replace('(', '').replace(')', '').replace(',', '')


def city_grid(c):
    """Local UTM grid of 120 m cells centred on the city; the city-region is the circle of radius R."""
    zone = int((c.lon + 180) // 6) + 1
    epsg = (32600 if c.lat >= 0 else 32700) + zone
    tr = Transformer.from_crs(4326, epsg, always_xy=True)
    x0, y0 = tr.transform(c.lon, c.lat)
    R = float(c.R_km) * 1000; half = R + 1200
    n = int(math.ceil(2 * half / CELL))
    xmin = math.floor((x0 - half) / CELL) * CELL; ymax = math.ceil((y0 + half) / CELL) * CELL
    transform = from_origin(xmin, ymax, CELL, CELL)
    xs = xmin + CELL * (np.arange(n) + 0.5); ys = ymax - CELL * (np.arange(n) + 0.5)
    X, Y = np.meshgrid(xs, ys)
    return dict(epsg=epsg, transform=transform, shape=(n, n), x0=x0, y0=y0, R=R, dist=np.hypot(X - x0, Y - y0), X=X, Y=Y)
