"""Within-city analyses for one city-region (sealing estimands only).
Epoch index k: 0 = 1985-1989, 1 = 1998-2002, 2 = 2012-2016, 3 = 2021-2025. Effects per ten percentage points of
impervious cover (ISA) on heat-island intensity HI (degC)."""
import sys, os, json, time, numpy as np, pandas as pd, lightgbm as lgb, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
import est as E
W0 = E.TERRAIN; WL = E.TERRAIN + E.LOC; NMAX = 15000
OUT = f'{RES}/city'; os.makedirs(OUT, exist_ok=True); os.makedirs(f'{DATA}/hi', exist_ok=True)


def keep(o, pre):
    return {f'{pre}_{k}': float(v) for k, v in o.items() if np.isscalar(v)}


def run(c):
    s = slug(c); fo = f'{OUT}/{s}.json'
    if os.path.exists(fo): return 'skip'
    t0 = time.time()
    df = pd.read_parquet(f'{DATA}/cells2/{s}.parquet')
    if len(df) > NMAX: df = df.sample(NMAX, random_state=0).sort_values('cell').reset_index(drop=True)
    for k in range(4):
        for v in ['lst', 'ndvi', 'albedo', 'isa', 'tree', 'ndvi20', 'ndvi80', 'mndwi', 'ndbi']:
            if f'{v}{k}' not in df: df[f'{v}{k}'] = np.nan
    R = dict(city=c, n_cells=len(df), epochs_available=int(sum(df[f'lst{k}'].notna().mean() > 0.5 for k in range(4))))
    df['isa_wc'] = df['wc_built']
    for k in range(4):
        if f'lst{k}' not in df or df[f'lst{k}'].isna().mean() > 0.5: df[f'hi{k}'] = np.nan; continue
        col = 'isa_wc' if k == 3 else f'isa{k}'
        df[f'hi{k}'], R[f'lapse{k}'], R[f'nrural{k}'] = E.heat_island(df, k, col)
        R[f'uhi_core{k}'] = float(np.nanmedian(df.loc[df.nb1k_isa >= 0.5, f'hi{k}'])) if (df.nb1k_isa >= 0.5).sum() > 50 else np.nan
    for k in range(4):
        df[f'D{k}'] = df[f'isa{k}'] * 10
    df['Dwc'] = df['isa_wc'] * 10
    folds = E.folds_by_block(df['blk2'].values)
    R['urban_share'] = float((df.nb1k_isa >= 0.5).mean()); R['fringe_share'] = float(((df.nb1k_isa >= 0.1) & (df.nb1k_isa < 0.5)).mean())

    # 1. main cross-section 2021-2025, WorldCover ISA, mediators NDVI, albedo (Landsat) and tree cover (WorldCover)
    m = df[['hi3', 'Dwc', 'ndvi3', 'albedo3', 'wc_tree'] + WL].notna().all(1)
    d = df[m].reset_index(drop=True); fd = folds[m.values]
    o = E.dml(d, 'hi3', 'Dwc', WL, cat=['bin5'], mediators=('ndvi3', 'albedo3', 'wc_tree'), folds=fd)
    R.update(keep(o, 'cs3')); R['cs3_sd_D'] = float(d.Dwc.std())
    # tree-only mediation (independent of Landsat)
    Mt = o['Mt'][:, [2]]; bj, sej, _ = E.ols_cluster(o['Yt'], np.column_stack([o['Dt'], Mt]), d['blk2'].values)
    a, ase, _ = E.ols_cluster(Mt[:, 0], o['Dt'], d['blk2'].values)
    R.update(cs3t_direct=bj[0], cs3t_direct_se=sej[0], cs3t_path_tree=a[0] * bj[1], cs3t_path_tree_se=float(np.sqrt((a[0] * sej[1]) ** 2 + (bj[1] * ase[0]) ** 2)))
    # sensitivity: refit without location bins (benchmark)
    o0 = E.dml(d, 'hi3', 'Dwc', W0, folds=fd)
    R.update(keep(E.sensitivity(o['Yt'], o['Dt'], o['e'], o['theta'], o['se'], o0['Yt'], o0['Dt'], o0['e']), 'sens'))
    R['cs3_theta_nobins'] = o0['theta']; R['cs3_se_nobins'] = o0['se']
    # residuals for the transfer model
    tr = d[['cell', 'wc_tree', 'wc_built', 'nb1k_isa', 'ndvi3']].copy(); tr['Yt'] = o['Yt']; tr['Dt'] = o['Dt']
    tr.sample(min(len(tr), 3000), random_state=0).to_parquet(f'{DATA}/hi/{s}_resid.parquet', index=False)
    # negative-control outcome: 1985-1989 heat island regressed on 2021-2025 WorldCover ISA among cells that the
    # back-cast shows as unsealed in 1985-1989 (sealing after 1989 cannot cause the earlier heat island)
    mm = df[['hi0', 'Dwc', 'D0'] + WL].notna().all(1) & (df.isa0 < 0.05)
    if mm.sum() > 2000 and df.loc[mm, 'Dwc'].std() > 0.2:
        dd = df[mm].reset_index(drop=True); oo = E.dml(dd, 'hi0', 'Dwc', WL + ['D0'], cat=['bin5'], folds=folds[mm.values])
        R.update(nco_theta=oo['theta'], nco_se=oo['se'], nco_n=int(mm.sum()))

    # 2. strata of the 2021-2025 cross-section (1-km neighbourhood impervious cover)
    for nm, lo, hi in [('core', 0.5, 1.01), ('fringe', 0.1, 0.5), ('rural', -1, 0.1)]:
        ms = m & (df.nb1k_isa >= lo) & (df.nb1k_isa < hi)
        if ms.sum() >= 600 and df.loc[ms, 'Dwc'].std() > 0.3:
            ds_ = df[ms].reset_index(drop=True); oo = E.dml(ds_, 'hi3', 'Dwc', WL, cat=['bin5'], folds=folds[ms.values])
            R.update({f'st_{nm}_theta': oo['theta'], f'st_{nm}_se': oo['se'], f'st_{nm}_n': int(ms.sum())})

    # 3. cross-sections of all epochs with back-cast ISA (consistent product)
    for k in range(4):
        mk = df[[f'hi{k}', f'D{k}', f'ndvi{k}', f'albedo{k}', f'tree{k}'] + WL].notna().all(1)
        if mk.sum() < 3000: continue
        dk = df[mk].reset_index(drop=True)
        oo = E.dml(dk, f'hi{k}', f'D{k}', WL, cat=['bin5'], mediators=(f'ndvi{k}', f'albedo{k}'), folds=folds[mk.values])
        R.update({f'bc{k}_theta': oo['theta'], f'bc{k}_se': oo['se'], f'bc{k}_direct': oo['direct'], f'bc{k}_direct_se': oo['direct_se'],
                  f'bc{k}_r2_DW': oo['r2_DW']})

    # 4. first differences (back-cast ISA), adjusting for terrain, location and baseline ISA
    for a_, b_ in [(0, 3), (1, 3), (2, 3), (0, 1), (1, 2)]:
        df['dY'] = df[f'hi{b_}'] - df[f'hi{a_}']; df['dD'] = df[f'D{b_}'] - df[f'D{a_}']
        mk = df[['dY', 'dD', f'D{a_}'] + WL].notna().all(1)
        if mk.sum() < 3000: continue
        dk = df[mk].reset_index(drop=True)
        oo = E.dml(dk, 'dY', 'dD', WL + [f'D{a_}'], cat=['bin5'], folds=folds[mk.values])
        R.update({f'fd{a_}{b_}_theta': oo['theta'], f'fd{a_}{b_}_se': oo['se'], f'fd{a_}{b_}_n': int(mk.sum()),
                  f'fd{a_}{b_}_nchg': int((dk.dD.abs() >= 0.5).sum())})

    # 5. dated conversion: event-study style tests with back-cast (bc) and ESA CCI (cci) dating
    designs = []
    if 'cci_urban_1992' in df:
        designs += [('cciA', (df.cci_urban_1992 < 0.05) & (df.cci_urban_2000 < 0.05), (df.cci_urban_2014 - df.cci_urban_2000) * 10, {'pre1': (0, 1), 'post': (1, 2), 'post2': (2, 3)}),
                    ('cciB', (df.cci_urban_2000 < 0.05) & (df.cci_urban_2014 < 0.05), (df.cci_urban_2020 - df.cci_urban_2014) * 10, {'pre2': (0, 1), 'pre1': (1, 2), 'post': (2, 3)})]
    designs += [('bcA', (df.isa0 < 0.1) & (df.isa1 < 0.1), df.D2 - df.D1, {'pre1': (0, 1), 'post': (1, 2), 'post2': (2, 3)}),
                ('bcB', (df.isa0 < 0.1) & (df.isa1 < 0.1) & (df.isa2 < 0.1), df.D3 - df.D2, {'pre2': (0, 1), 'pre1': (1, 2), 'post': (2, 3)})]
    for nm, base, dose, per in designs:
        df['dose'] = dose.clip(lower=0)
        need = [f'hi{k}' for k in range(4)]
        mk = base & df['dose'].notna() & df[need + WL].notna().all(1)
        ntr = int((mk & (df['dose'] >= 1)).sum()); R[f'{nm}_ntreated'] = ntr
        if ntr < 50 or mk.sum() < 2000: continue
        dk = df[mk].reset_index(drop=True); fk = folds[mk.values]
        Dt = E.resid(dk['dose'].values, dk[WL], fk, ['bin5'])
        for pn, (a_, b_) in per.items():
            dk['dY'] = dk[f'hi{b_}'] - dk[f'hi{a_}']
            oo = E.dml(dk, 'dY', 'dose', WL, cat=['bin5'], folds=fk, Dt_given=Dt)
            R.update({f'{nm}_{pn}_theta': oo['theta'], f'{nm}_{pn}_se': oo['se']})

    # 6. within-city gradient boosting with location bins (fair comparison with DML): +10 pp ISA in every cell,
    # cross-fitted predictions, minimal (ISA + terrain + location) and full (+ NDVI, albedo, tree cover)
    for nm, F in [('gbm_min', ['Dwc'] + WL), ('gbm_full', ['Dwc', 'ndvi3', 'albedo3', 'wc_tree'] + WL)]:
        eff = np.full(len(d), np.nan); effj = np.full(len(d), np.nan)
        for f in np.unique(fd):
            trn, tst = fd != f, fd == f
            mdl = lgb.train(E.NP, lgb.Dataset(d.loc[trn, F], d.loc[trn, 'hi3'], categorical_feature=['bin5']), E.NR)
            X1 = d.loc[tst, F].copy(); p0 = mdl.predict(X1); X1['Dwc'] = np.minimum(X1['Dwc'] + 1, 10)
            eff[tst] = mdl.predict(X1) - p0
            if nm == 'gbm_full':
                for mcol in ['ndvi3', 'albedo3', 'wc_tree']: X1[mcol] = X1[mcol] + R[f'cs3_a_{mcol}']
                effj[tst] = mdl.predict(X1) - p0
        R[f'{nm}_eff'] = float(np.nanmean(eff))
        if nm == 'gbm_full': R['gbm_full_joint_eff'] = float(np.nanmean(effj))
    # save HI table for transfer analyses
    keepc = ['cell', 'dx', 'dy', 'dist', 'rdist', 'nb1k_isa', 'wc_tree', 'wc_built'] + W0 + \
            [f'{v}{k}' for k in range(4) for v in ['hi', 'isa', 'tree', 'ndvi', 'albedo']]
    df[[x for x in keepc if x in df]].to_parquet(f'{DATA}/hi/{s}.parquet', index=False)
    R['runtime_s'] = round(time.time() - t0, 1)
    json.dump({k: (None if (isinstance(v, float) and not np.isfinite(v)) else v) for k, v in R.items()}, open(fo, 'w'))
    return R['runtime_s']


if __name__ == '__main__':
    sel = (open(sys.argv[1][1:]).read().split('\n') if sys.argv[1:] and sys.argv[1].startswith('@') else sys.argv[1:]) or list(cities().city)
    for c in sel:
        if not c: continue
        try: print(c, run(c), flush=True)
        except Exception as ex:
            import traceback; traceback.print_exc(); print('FAILED', c, flush=True)
