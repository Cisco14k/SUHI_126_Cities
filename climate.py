"""City climate descriptors (TerraClimate 1991-2020) and CMIP6 (NEX-GDDP) delta-change projections of the
descriptors for 2041-2070 and 2071-2100 under SSP2-4.5 and SSP5-8.5 (baseline 1995-2014 of each model).
Future aridity uses a Hargreaves-type PET scaling with the change of warm-season maximum temperature; future VPD
assumes unchanged relative humidity (Clausius-Clapeyron scaling); soil moisture and wind are held fixed."""
import sys, os, glob, pickle, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
MODELS = ['GFDL-ESM4', 'IPSL-CM6A-LR', 'MPI-ESM1-2-HR', 'MRI-ESM2-0', 'UKESM1-0-LL']
PERIODS = {'2041-2070': (2041, 2070), '2071-2100': (2071, 2100)}


def descriptors():
    tc = pickle.load(open(f'{DATA}/terraclimate.pkl', 'rb')); cs = cities(); rows = []
    for _, c in cs.iterrows():
        d = tc[c.city]; s = {v: d[v].mean(['lat', 'lon'], skipna=True).to_series()['1991':'2020'] for v in d}
        clim = {v: s[v].groupby(s[v].index.month).mean() for v in s}
        wm = sorted(clim['tmax'].sort_values(ascending=False).index[:3].tolist())
        rows.append(dict(city=c.city, warm_months='-'.join(map(str, wm)), tmax_warm=clim['tmax'][wm].mean(), tmin_warm=clim['tmin'][wm].mean(),
                         ppt=clim['ppt'].sum(), pet=clim['pet'].sum(), aridity=clim['ppt'].sum() / max(clim['pet'].sum(), 1),
                         vpd_warm=clim['vpd'][wm].mean(), soil=clim['soil'].mean(), ws=clim['ws'].mean(), aet=clim['aet'].sum(),
                         tmax_warm_1985_89=s['tmax'].index.size and d['tmax'].mean(['lat', 'lon']).to_series()['1985':'1989'].pipe(lambda x: x[x.index.month.isin(wm)].mean())))
    df = pd.DataFrame(rows).merge(cs[['city', 'country', 'region', 'koppen_ms', 'lat', 'lon', 'pop', 'R_km']], on='city')
    df['zone'] = df.koppen_ms.str[0].map(dict(A='Tropical', B='Arid', C='Temperate', D='Continental', E='Polar'))
    df.to_csv(f'{RES}/city_climate.csv', index=False); return df


def es(T):  # saturation vapour pressure (kPa)
    return 0.6108 * np.exp(17.27 * T / (T + 237.3))


def cmip6_deltas(clim):
    cty = pd.read_csv(f'{DATA}/cities.csv'); rows = []
    wm = [list(map(int, w.split('-'))) for w in clim.set_index('city').loc[cty.city, 'warm_months']]
    def load(model, scen, y0, y1, var):
        fs = [f for f in glob.glob(f'{DATA}/cmip6/{model}_{scen}_*_{var}.npz') if y0 <= int(f.split('_')[-2]) <= y1]
        return np.nanmean([np.load(f)['mm'] for f in fs], 0) if fs else None, len(fs)
    for m in MODELS:
        bt, nb = load(m, 'historical', 1995, 2014, 'tasmax'); bp, _ = load(m, 'historical', 1995, 2014, 'pr')
        if bt is None: continue
        for scen in ['ssp245', 'ssp585']:
            for pn, (y0, y1) in PERIODS.items():
                ft, nf = load(m, scen, y0, y1, 'tasmax'); fp, _ = load(m, scen, y0, y1, 'pr')
                if ft is None: continue
                for i, c in enumerate(cty.city):
                    w = [x - 1 for x in wm[i]]
                    dT = ft[w, i].mean() - bt[w, i].mean(); dTa = ft[:, i].mean() - bt[:, i].mean()
                    rP = fp[:, i].mean() / max(bp[:, i].mean(), 1e-3)
                    rows.append(dict(city=c, model=m, scen=scen, period=pn, dtmax_warm=dT, dtmax_ann=dTa, rppt=rP, nyears_base=nb, nyears_fut=nf))
    D = pd.DataFrame(rows).merge(clim[['city', 'tmax_warm', 'tmin_warm', 'aridity', 'vpd_warm', 'soil', 'ws', 'ppt', 'pet']], on='city')
    tm = (D.tmax_warm + D.tmin_warm) / 2
    D['rpet'] = (tm + D.dtmax_ann + 17.8) / (tm + 17.8)
    D['tmax_warm_f'] = D.tmax_warm + D.dtmax_warm
    D['aridity_f'] = D.aridity * D.rppt / D.rpet
    D['vpd_warm_f'] = D.vpd_warm * es(D.tmax_warm_f) / es(D.tmax_warm)
    D['soil_f'] = D.soil; D['ws_f'] = D.ws
    D.to_csv(f'{RES}/cmip6_deltas.csv', index=False); return D


if __name__ == '__main__':
    clim = descriptors(); print(clim.zone.value_counts())
    if len(sys.argv) > 1 and sys.argv[1] == 'cmip6':
        D = cmip6_deltas(clim); print(D.groupby(['scen', 'period']).dtmax_warm.describe())
