"""Monthly TerraClimate (1985-2025 where available) in a box around each city: warm season, Koppen class, climate descriptors."""
import pystac_client, planetary_computer as pc, xarray as xr, numpy as np, pandas as pd, pickle, time, dask, sys
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
dask.config.set(scheduler='threads', num_workers=8)
cs = cities()
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
tc = cat.get_collection("terraclimate").assets['zarr-abfs']
ds = xr.open_dataset(tc.href, **tc.extra_fields['xarray:open_kwargs'])
out = {}; t0 = time.time()
for var in ['tmax', 'tmin', 'ppt', 'pet', 'soil', 'ws', 'vpd', 'aet']:
    sel = [ds[var].sel(lat=slice(c.lat + 0.45, c.lat - 0.45), lon=slice(c.lon - 0.55, c.lon + 0.55), time=slice('1985-01-01', '2025-12-31')) for _, c in cs.iterrows()]
    res = dask.compute(*sel)
    for (i, c), r in zip(cs.iterrows(), res): out.setdefault(c.city, {})[var] = r
    print(var, round(time.time() - t0), flush=True)
pickle.dump(out, open(f'{DATA}/terraclimate.pkl', 'wb')); print('done')
