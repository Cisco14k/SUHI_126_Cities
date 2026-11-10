"""126 city-regions of the study (SI Table 1 of the submitted manuscript), geocoded with Natural Earth populated places."""
import json, unicodedata, numpy as np, pandas as pd
ROOT = '/home/claude/w126'
def norm(s): return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('-', ' ').replace("'", '').strip()
ALIAS = {'Copenhagen': 'København', 'Kyiv': 'Kiev', 'Washington DC': 'Washington, D.C.', 'Mount Hagen': 'Mt.  Hagen'}
CMAP = {'Congo (Kinshasa)': 'Congo (Kinshasa)', 'United States of America': 'United States of America'}
g = json.load(open('/home/claude/work/data/ne/pp.geojson'))
pp = pd.DataFrame([f['properties'] for f in g['features']]); pp['n'] = pp.NAMEASCII.map(norm); pp['nn'] = pp.NAME.map(norm)
c = pd.read_csv(f'{ROOT}/data/cities126.csv')
out = []
for _, r in c.iterrows():
    key = norm(ALIAS.get(r.city, r.city))
    m = pp[(pp.n == key) | (pp.nn == key)]
    if len(m) > 1:
        mc = m[m.ADM0NAME.map(norm).str.contains(norm(r.country)[:5]) | m.SOV0NAME.map(norm).str.contains(norm(r.country)[:5])]
        m = mc if len(mc) else m
        m = m.sort_values('POP_MAX', ascending=False)
    if not len(m): print('MISSING', r.city); continue
    x = m.iloc[0]
    out.append(dict(city=r.city, country=r.country, region=r.region, koppen_ms=r.koppen, lat=float(x.LATITUDE), lon=float(x.LONGITUDE), pop=float(x.POP_MAX), ne_country=x.ADM0NAME))
df = pd.DataFrame(out)
df['R_km'] = np.clip(25 + 10 * np.log10(np.maximum(df['pop'], 1e5) / 1e5), 25, 45)
df.to_csv(f'{ROOT}/data/cities.csv', index=False)
print(len(df)); print(df[df.country.map(norm).str[:5] != df.ne_country.map(norm).str[:5]][['city', 'country', 'ne_country', 'lat', 'lon']])
