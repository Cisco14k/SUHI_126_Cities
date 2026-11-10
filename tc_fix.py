import pickle, xarray as xr, pystac_client, planetary_computer as pc, sys
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
cs = cities(); cs = cs[cs.city.str.startswith('San Luis')]
cat = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1", modifier=pc.sign_inplace)
tc = cat.get_collection("terraclimate").assets['zarr-abfs']
ds = xr.open_dataset(tc.href, **tc.extra_fields['xarray:open_kwargs'])
out = pickle.load(open(f'{DATA}/terraclimate.pkl', 'rb')); out.pop('San Luis', None)
for _, c in cs.iterrows():
    out[c.city] = {v: ds[v].sel(lat=slice(c.lat + 0.45, c.lat - 0.45), lon=slice(c.lon - 0.55, c.lon + 0.55), time=slice('1985-01-01', '2025-12-31')).load() for v in ['tmax', 'tmin', 'ppt', 'pet', 'soil', 'ws', 'vpd', 'aet']}
    print(c.city, flush=True)
pickle.dump(out, open(f'{DATA}/terraclimate.pkl', 'wb')); print(len(out))
