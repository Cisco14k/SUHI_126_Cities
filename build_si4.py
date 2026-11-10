"""Supplementary Information (notes and tables, Nature three-rule tables) and Source Data workbook."""
import sys, json, glob, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from docxbuild import Doc
from build_ms import S, m, rng, B, pct, OUT
from build_ms2 import R3, DEC
TITLE = 'Predictive accuracy does not reveal the daytime surface heat cost of sealing urban land'
R4 = S['r4']; R5 = S['r5']
from summarize import load_own
own, clim = load_own()
ZONES = ['All', 'Tropical', 'Arid', 'Temperate', 'Continental']


def pooled_row(lab, key):
    out = [lab]
    for z in ZONES:
        p = S.get(key, {}).get(z)
        out.append(f"{m(p['mu'])} ({rng(p['lo'], p['hi'])}); {p['k']}" if p and np.isfinite(p['mu']) else '—')
    return out


def build():
    D = Doc(line_numbers=False, spacing=1.15, size=10)
    D.para('**Supplementary Information**', size=14, after=6)
    D.para(f'**{TITLE}**', size=12, after=12)
    D.h('Supplementary Note 1 | City-regions, selection and representativeness', 2)
    D.para(f"The {S['n_cities']} city-regions were selected with the rules in Methods, eighteen per world region, in 62 countries. Eight city-regions (Chengdu, Kashgar, Lhasa, Nanjing, Qingdao and Shenzhen in China; Koforidua and Yendi in Ghana) were taken from a pre-specified list of rapidly growing cities in two countries; all others were drawn by the selection rules. Three selected areas with systematic gaps in the Landsat Collection 2 surface-temperature product (missing ASTER GED emissivity) were replaced before any analysis (Guayaquil by Fortaleza, Honiara by Port Moresby, St John's by Toronto); because the gaps arise from the emissivity database rather than from surface properties, the replacement is unlikely to be related to the effect of sealing, but it removes three coastal cities from the sample. Removing all eleven purposively included or replacement city-regions changed the pooled total effect from {m(S['total_wc']['All']['mu'])} to {m(R3['excl_purposive']['mu'])} °C. The design balances world regions and climates; it does not represent the world's urban population, and large cities of South and East Asia are under-represented relative to their population. La Paz, the only city-region with a polar (high-altitude tundra) Köppen class, is listed in all tables but excluded from zone summaries. In the median city-region {pct(S['urban_share_median'])} of the sampled land cells lie in urban cores (1-km impervious cover of at least 50%) and {pct(S['fringe_share_median'])} in fringes (10–50%); effects are therefore also reported by stratum (Fig. 2d). Analyses use circular city-regions; administrative boundaries were not used.")
    D.h('Supplementary Note 2 | Identification assumptions', 2)
    D.para("The total effect of sealing is identified within a city-region if (i) conditional on terrain and 5-km location bins W there is no unmeasured common cause of impervious cover and surface heat (conditional exchangeability), (ii) every cell has a positive chance of the observed range of impervious cover given W (overlap), (iii) a cell's heat depends on its own sealing and not on that of neighbours beyond what W captures (no interference at 120 m), and (iv) the partially linear model describes the variance-weighted average effect. Assumption (i) is the weakest: irrigation, land management, socioeconomic conditions and redevelopment can affect both. The negative-control outcome tests one implication of (i), the dated-conversion designs another, and the Cinelli–Hazlett bounds quantify how strong a violation would need to be. The direct effect additionally requires no unmeasured mediator–outcome confounding, and the product-of-coefficients decomposition assumes no interaction between sealing and the mediators; we therefore report the decomposition as descriptive. Assumption (iii) is likely violated at the scale of a few hundred metres, where surrounding sealing raises a cell's temperature; such spillovers would bias the cell-level effect towards zero relative to the effect of sealing a whole neighbourhood.")
    D.h('Supplementary Note 3 | CMIP6 projections', 2)
    D.para("The five models are the primary ISIMIP3b selection, which spans the range of climate sensitivity of CMIP6. NEX-GDDP-CMIP6 provides daily bias-corrected, spatially disaggregated fields at 0.25°. To keep the extraction tractable, every fourth day was used (monthly means from 91 days per year) and every second (historical) or third (future) year within each period; tests on one model showed that the sampling changes 30-year warm-season means by less than 0.1 °C. Changes were computed per model against its own 1995–2014 baseline and applied as deltas to TerraClimate 1991–2020, which avoids residual biases of the downscaled fields. The projection evaluates the causal transfer model at future climate descriptors with each city's present surface; it is a space-for-time substitution that assumes the present relation between climate and the effect of sealing holds under future climates, and it does not include future vegetation change, irrigation or CO~2~ effects on transpiration.")
    # tables
    D.h('Supplementary Tables', 1)
    t1 = own.reset_index().sort_values(['region', 'city'])
    rows = [[r.city, r.country, r.region.replace('C. America & Caribbean', 'C. Am. & Carib.'), r.zone, f"{m(r.cs3_theta)} ({rng(r.cs3_theta - 1.96 * r.cs3_se, r.cs3_theta + 1.96 * r.cs3_se)})",
             m(r.cs3_direct), m(r.fd03_theta) if np.isfinite(r.fd03_theta) else '—', m(r.sens_rv), pct(r.urban_share)] for r in t1.itertuples()]
    D.table(['City-region', 'Country', 'Region', 'Zone', 'Total effect (95% CI)', 'Direct', 'First diff. 1985–2025', 'RV', 'Core share'], rows,
            widths_mm=[28, 22, 22, 18, 30, 12, 15, 10, 12], size=7,
            caption='**Supplementary Table 1 | City-regions and within-city effects, 2021–2025.** Effects in °C per ten percentage points of impervious cover; RV, Cinelli–Hazlett robustness value; core share, share of sampled cells with 1-km impervious cover of at least 50%.')
    D.table(['Dataset', 'Use', 'Resolution, period', 'Access'],
            [['Landsat Collection 2 Level-2 (TM, ETM+, OLI, OLI-2)', 'Surface temperature, reflectance', '30 m, 1985–2025', 'Planetary Computer'],
             ['ESA WorldCover 2021 v200', 'Impervious, tree cover 2021', '10 m', 'Planetary Computer'],
             ['ESA CCI land cover (C3S)', 'Independent urban dating', '300 m, 1992–2020', 'Planetary Computer'],
             ['LCMAP CONUS v1.3', 'Independent developed cover (US)', '30 m, 1985–2021', 'Planetary Computer'],
             ['Copernicus GLO-30 DEM', 'Terrain, lapse-rate adjustment', '30 m', 'Planetary Computer'],
             ['TerraClimate', 'Warm season, climate descriptors', '~4 km, 1985–2021', 'Planetary Computer'],
             ['NEX-GDDP-CMIP6', 'Projected climate deltas', '0.25°, 1995–2100', 'Planetary Computer'],
             ['GlobPOP', 'Population context', '~1 km, 2020', 'Zenodo'],
             ['Natural Earth', 'City locations, map', '1:10 m', 'naturalearthdata.com']],
            widths_mm=[50, 45, 32, 30], size=8, caption='**Supplementary Table 2 | Data sources.**')
    keys = [('Total, WorldCover 2021–2025', 'total_wc'), ('Direct', 'direct'), ('Path via NDVI', 'path_ndvi'), ('Path via albedo', 'path_albedo'), ('Path via tree cover (joint)', 'path_tree_joint'),
            ('Path via tree cover (tree only)', 'path_tree_only'), ('Total, terrain only (no location bins)', 'total_nobins'), ('Urban core', 'core'), ('Fringe', 'fringe'), ('Rural', 'rural'),
            ('Cross-section 1985–1989 (back-cast)', 'bc0'), ('Cross-section 1998–2002', 'bc1'), ('Cross-section 2012–2016', 'bc2'), ('Cross-section 2021–2025 (back-cast)', 'bc3'),
            ('First difference 1985–2025', 'fd03'), ('First difference 1998–2025', 'fd13'), ('First difference 2012–2025', 'fd23'), ('First difference 1985–2002', 'fd01'), ('First difference 1998–2016', 'fd12'),
            ('Negative control (1985–1989 HI)', 'nco')]
    D.table(['Estimand'] + ZONES, [pooled_row(l, k) for l, k in keys], widths_mm=[42, 24, 24, 24, 24, 24], size=7,
            caption='**Supplementary Table 3 | Random-effects pooled within-city estimates.** °C per ten percentage points, 95% CI in parentheses; number of city-regions after the semicolon.')
    rows = []
    for dsg in ['six', 'zone', 'continent', 'six_urban', 'zone_urban', 'continent_urban']:
        for mm in ['causal', 'minimal', 'minimal_loc', 'partial', 'full', 'full_loc', 'full_mono']:
            v = S['change'].get(f'{dsg}|{mm}')
            if v: rows.append([dsg.replace('_urban', ', urban/fringe cells'), mm.replace('_', ' '), B(v['rho']), B(v['r2']), B(v['slope']), v['n']])
    D.table(['Design', 'Model', 'Spearman ρ', 'R²', 'Calibration slope', 'Cities'], rows, widths_mm=[36, 26, 28, 28, 28, 12], size=7,
            caption='**Supplementary Table 4 | Prediction of 1985–2025 change in held-out cities.** Medians over held-out cities with 95% bootstrap intervals.')
    K = pd.read_csv(f'{RES}/conformal.csv')
    rows = [[r, mm, pct(g.cover.median()), pct(g.cover_group.median()) if np.isfinite(g.cover_group.median()) else '—', m(g.q90.median(), 1)] for (mm, r), g in K.groupby(['model', 'region'])]
    D.table(['Region', 'Model', 'Coverage, all other cities', 'Coverage, same continent', 'Half-width (°C)'], rows, widths_mm=[36, 20, 30, 30, 24], size=7,
            caption='**Supplementary Table 5 | Split-conformal 90% intervals for single cells by region (six-out design).**')
    rows = []
    for d, lab in [('cciA', 'CCI dating, converted 2000–2014'), ('cciB', 'CCI dating, converted 2014–2020'), ('bcA', 'Back-cast dating, converted 1998–02 to 2012–16'), ('bcB', 'Back-cast dating, converted 2012–16 to 2021–25')]:
        for pn, pl in [('pre2', '2 epochs before'), ('pre1', '1 epoch before'), ('post', 'conversion epoch'), ('post2', '1 epoch after')]:
            p = S.get(f'{d}_{pn}', {}).get('All')
            if p and np.isfinite(p['mu']): rows.append([lab, pl, f"{m(p['mu'], 3)} ({rng(p['lo'], p['hi'], 3)})", p['k']])
    D.table(['Design', 'Period', 'Coefficient (°C per 10 pp converted)', 'Cities'], rows, widths_mm=[60, 30, 50, 14], size=7.5,
            caption='**Supplementary Table 6 | Dated-conversion designs.** Change of heat-island intensity per ten percentage points of conversion in each period, random-effects pooled (95% CI).')
    if S.get('sim'):
        rows = []
        for sc in ['A', 'B03', 'B05', 'B08', 'C']:
            v = S['sim'][sc]
            for e, lab in [('dml_total', 'DML total'), ('dml_direct', 'DML direct'), ('gbm_min_bins', 'GBM minimal + bins'), ('gbm_full_bins', 'GBM full + bins'), ('gbm_full_bins_joint', 'GBM full, shifted'), ('gbm_min_nobins', 'GBM minimal, no bins')]:
                rows.append([sc, lab, m(v['true_direct'] if e in ('dml_direct', 'gbm_full_bins') else v['true_total']), m(v[e]['median']), m(v[e]['bias'], 3), m(v[e]['rmse'], 3),
                             pct(v['cover_total']) if e == 'dml_total' else (pct(v['cover_direct']) if e == 'dml_direct' else '—')])
        D.table(['Scenario', 'Estimator', 'True (median)', 'Estimate (median)', 'Bias', 'RMSE', '95% CI coverage'], rows, widths_mm=[16, 34, 20, 22, 18, 18, 22], size=7,
                caption=f"**Supplementary Table 7 | Simulations with known effects.** {S['sim']['A']['ncity']} city-regions, five replicates per scenario. A, no unmeasured confounding; B03/B05/B08, unmeasured confounder with correlation 0.3/0.5/0.8 with block-mean sealing; C, nonlinear and heterogeneous effects. Direct-effect estimators are compared with the true direct effect, others with the true total effect.")
    if S.get('proj'):
        rows = []
        for k, v in S['proj'].items():
            sc, pe = k.split('|')
            rows.append([sc.upper().replace('SSP245', 'SSP2-4.5').replace('SSP585', 'SSP5-8.5'), pe.replace('-', '–'), m(v['dT_median'], 1), f"{m(v['d_tau_median'])} ({m(v['d_tau_q25'])} to {m(v['d_tau_q75'])})",
                         pct(v['share_increase']), pct(v['share_gcm_agree']), pct(v['share_extrap'])] + [m(v['by_zone'].get(z, np.nan)) for z in ZONES[1:]])
        D.table(['Scenario', 'Period', 'ΔTmax warm (°C)', 'Δ heat cost (IQR)', 'Increase', 'GCMs agree', 'Extrapolating'] + ZONES[1:], rows, widths_mm=[16, 16, 14, 26, 13, 13, 15, 13, 12, 14, 15], size=6.5,
                caption=f"**Supplementary Table 8 | Heat cost of sealing in fringe cells under projected climates.** Change against the present (median city {m(S['proj_present_median'])} °C per ten percentage points); medians over cities of the five-model median; zone columns give median change.")
    bt = S.get('backcast_temporal', {}); bc = S['backcast_cv']
    rows = [['Impervious, spatial-block CV R² 2021–2025', m(bc.get('isa_r2'))], ['Tree cover, spatial-block CV R² 2021–2025', m(bc.get('tree_r2'))]]
    for k, lab in [('cci_lev0', 'r with CCI urban, 1985–1989 vs 1992'), ('cci_lev1', 'r with CCI, 1998–2002 vs 2000'), ('cci_lev2', 'r with CCI, 2012–2016 vs 2014'), ('cci_lev3', 'r with CCI, 2021–2025 vs 2020'),
                   ('cci_chg13', 'r of changes with CCI, 2000–2020'), ('cci_chg03', 'r of changes with CCI, 1992–2020'), ('cci_chg03_mean_bc', 'Mean change 1985–2025, back-cast'), ('cci_chg03_mean_cci', 'Mean change 1992–2020, CCI'),
                   ('lc_lev0', 'r with LCMAP, 1985–1989 vs 1987'), ('lc_lev3', 'r with LCMAP, 2021–2025 vs 2021'), ('lc_chg03', 'r of changes with LCMAP, 1987–2021'), ('lc_chg13', 'r of changes with LCMAP, 2000–2021')]:
        if k in bt: rows.append([lab, m(bt[k], 3)])
    D.table(['Check', 'Median over city-regions'], rows, widths_mm=[100, 40], size=8,
            caption=f"**Supplementary Table 9 | Validation of the back-cast.** Correlations of 1.2-km block means; LCMAP for {S.get('backcast_temporal_n_lcmap', 0)} US city-regions.")
    rows = []
    for key, lab in [('causal', 'Causal transfer'), ('minimal', 'GBM minimal'), ('minimal_loc', 'GBM minimal + location'), ('partial', 'GBM partial'), ('full', 'GBM full'), ('full_loc', 'GBM full + location'), ('full_mono', 'GBM full, monotone'), ('full_joint', 'GBM full, mediators shifted')]:
        v = S['intervention'].get(f'{key}_urban')
        if v: rows.append([lab, B(v['median']), B(v['mae_total']), B(v['mae_direct']), pct(v['sign'][0]), B(v['rho'])])
    D.table(['Model', 'Answer to +10 pp (°C)', 'MAD vs own total (°C)', 'MAD vs own direct (°C)', 'Sign agreement', 'ρ with own total'], rows, widths_mm=[40, 26, 26, 26, 18, 24], size=7.5,
            caption='**Supplementary Table 10 | Intervention test restricted to urban cores and fringes.** As Table 2, for cells with 1-km impervious cover of at least 10%, continent held out; 95% bootstrap intervals over cities.')
    rows = []
    def pr(lab, p): return [lab, f"{m(p['mu'])} ({rng(p['lo'], p['hi'])})", p['k']]
    for lab, k in [('Main adjustment set, all cells', None), ('Cells unsealed in 1985–1989, main set', 'lag_unsealed_ref'), ('  + 1985–1989 heat island and ISA', 'lag_unsealed'),
                   ('All cells, main set (same sample)', 'lag_all_ref'), ('  + 1985–1989 heat island and ISA', 'lag_all'), ('Inner half of radius', 'inner'), ('Without 11 purposive/replaced cities', 'excl_purposive'),
                   ('Own cell, estimated jointly with neighbourhood', 'sp_own'), ('1-km neighbourhood, estimated jointly', 'sp_nb')]:
        rows.append(pr(lab, S['total_wc']['All'] if k is None else R3[k]))
    for lab, k in [('Total effect, 2-km location bins', 'tot2'), ('Own cell, joint, 2-km location bins', 'sp2_own'), ('1-km neighbourhood, joint, 2-km location bins', 'sp2_nb'),
                   ('European city-regions, total effect', 'eu_total'), ('European, direct effect', 'eu_direct'), ('European, urban cores', 'eu_core'), ('European, fringes', 'eu_fringe'),
                   ('European, all cells + 1985–1989 heat island', 'eu_lag'), ('European, 1-km neighbourhood (joint)', 'eu_sp_nb')]:
        rows.append(pr(lab, R4[k]))
    rows.append(['Bias bound, confounder as strong as location bins', f"{m(S['sens_adj_pool']['mu'])} ({rng(S['sens_adj_pool']['lo'], S['sens_adj_pool']['hi'])})", S['sens_adj_pool']['k']])
    rows.append(['Standard errors × simulation calibration factor', f"{m(R3['total_calibrated']['mu'])} ({rng(R3['total_calibrated']['lo'], R3['total_calibrated']['hi'])})", R3['total_calibrated']['k']])
    D.table(['Design', 'Effect, °C per 10 pp (95% CI)', 'Cities'], rows, widths_mm=[85, 45, 16], size=7,
            caption=f"**Supplementary Table 11 | Lagged-outcome, spillover, location-bin, European and sample checks of the 2021–2025 total effect.** Random-effects pooled estimates. Simulation calibration factor ×{m(R3['se_inflation'])}; with it, {R3['sig_pos_calibrated']} city-regions have intervals above and {R3['sig_neg_calibrated']} below zero.")
    rows = []
    for d, lab in [('cA', 'Concordant (back-cast and CCI), 1998–02 to 2012–16'), ('cB', 'Concordant, 2012–16 to 2021–25')]:
        for pn, pl in [('pre2', '2 epochs before'), ('pre1', '1 epoch before'), ('post', 'conversion epoch'), ('post2', '1 epoch after')]:
            p = R3.get(f'{d}_{pn}')
            if p and np.isfinite(p['mu']): rows.append([lab, pl, f"{m(p['mu'], 3)} ({rng(p['lo'], p['hi'], 3)})", p['k']])
    for d, lab in [('cA', 'Concordant A'), ('bcA', 'Back-cast A'), ('bcB', 'Back-cast B'), ('cciA', 'CCI A'), ('cciB', 'CCI B'), ('cB', 'Concordant B')]:
        for t, tl in [('parallel', 'net of last pre-period'), ('linear', 'net of linear pre-trend')]:
            p = R3['adj'].get(d, {}).get(t)
            if p and np.isfinite(p['mu']): rows.append([lab, tl, f"{m(p['mu'], 3)} ({rng(p['lo'], p['hi'], 3)})", p['k']])
    D.table(['Design', 'Period or contrast', 'Coefficient (°C per 10 pp)', 'Cities'], rows, widths_mm=[62, 36, 44, 14], size=7.5,
            caption=f"**Supplementary Table 12 | Concordant dating and trend-adjusted contrasts.** Median {m(R3['cA_ntreated_median'], 0)} and {m(R3['cB_ntreated_median'], 0)} treated cells per city-region in concordant cohorts A and B; cohort B is too small for inference.")
    rows = [[f"{['1985–1989', '1998–2002', '2012–2016', '2021–2025'][int(k)]}", m(v, 2), m(R3['scenes'][k], 1)] for k, v in R3['overpass'].items()]
    D.table(['Epoch', 'Median local solar time of scenes (h)', 'Median usable scenes'], rows, widths_mm=[30, 55, 40], size=8,
            caption=f"**Supplementary Table 13 | Overpass time and scene numbers.** Within-city fixed-effects slopes of the epoch effect: {m(R3['temporal_climate_slope'][0], 3)} °C per °C of warm-season temperature (95% CI {rng(R3['temporal_climate_slope'][1], R3['temporal_climate_slope'][2], 3)}) and {m(R3['scene_slope'], 4)} °C per additional scene.")
    rows = [[k.split('|')[0].upper().replace('SSP245', 'SSP2-4.5').replace('SSP585', 'SSP5-8.5'), k.split('|')[1].replace('-', '–'), m(S['proj'][k]['d_tau_median'], 3), m(S['proj'][k]['d_tau_alt_median'], 3), m(v['median'], 3), rng(v['q10'], v['q90'], 3)] for k, v in R3['proj_nl'].items()]
    D.table(['Scenario', 'Period', 'Linear (main)', 'Climate-only modifiers', 'Nonlinear R-learner', 'Nonlinear, 10th–90th pct'], rows, widths_mm=[20, 20, 25, 30, 30, 34], size=7.5,
            caption='**Supplementary Table 14 | Change of the heat cost of sealing in fringe cells under projected climates, by transfer model** (°C per 10 pp; medians over cities of the five-model median).')
    rows = []
    for key, lab in [('causal_all', 'Causal transfer (linear)'), ('nl_all', 'Causal transfer (nonlinear)'), ('minimal_all', 'GBM minimal'), ('minimal_loc_all', 'GBM minimal + location'), ('partial_all', 'GBM partial'),
                     ('full_all', 'GBM full'), ('full_loc_all', 'GBM full + location'), ('full_mono_all', 'GBM full, monotone'), ('full_joint_all', 'GBM full, mediators shifted'), ('zone_baseline', 'Zone baseline')]:
        d = DEC[key]; xc = R4['ext']['conc'].get(key); xi = R4['ext']['cci'].get(key)
        rows.append([lab, m(d['median']), B(d['mae']), m(d['rho']), pct(d['tercile_agree'][0]), pct(d['top_recall']), pct(d['gross_misclass']),
                     B(xc['rho']) if xc else '—', f"{pct(xc['tercile'])}" if xc else '—', m(xi['rho'][0]) if xi else '—'])
    rows.append(["Cities' own total effect", '—', '—', '—', '—', '—', '—', B(R4['ext']['conc']['cs3_theta']['rho']), pct(R4['ext']['conc']['cs3_theta']['tercile']), m(R4['ext']['cci']['cs3_theta']['rho'][0])])
    D.table(['Model', 'Answer (°C)', 'MAD vs own (°C)', 'ρ vs own', 'Right third', 'Top third found', 'Off by two thirds', 'ρ vs concordant conversions', 'Right third (concordant)', 'ρ vs CCI conversions'], rows,
            widths_mm=[28, 12, 20, 11, 12, 12, 12, 22, 14, 13], size=6.5,
            caption=f"**Supplementary Table 15 | Screening performance against the cities' own estimates and against independent dated-conversion benchmarks.** Continent-out answers to +10 pp impervious cover. Concordant benchmark: {R4['ext']['conc']['n']} city-regions with ≥30 cells converted according to both products; CCI benchmark: {R4['ext']['cci']['n']} city-regions, noisier. European city-regions: mean absolute difference {m(R4['eu_mae']['causal_all'])} (causal), {m(R4['eu_mae']['full_all'])} (full), {m(R4['eu_mae']['zone_baseline'])} °C (zone baseline); Spearman ρ with own effects {m(R4['eu_rho']['causal_all'])}, {m(R4['eu_rho']['full_all'])} and {m(R4['eu_rho']['zone_baseline'])}.")
    rows = [["Lagged outcome, cells vegetated in 1985–1989: main set", f"{m(R5['lagveg_ref']['mu'])} ({rng(R5['lagveg_ref']['lo'], R5['lagveg_ref']['hi'])})", R5['lagveg_ref']['k']],
            ["  + 1985–1989 heat island and ISA", f"{m(R5['lagveg']['mu'])} ({rng(R5['lagveg']['lo'], R5['lagveg']['hi'])})", R5['lagveg']['k']],
            ["Concordant dating, CCI dose: before conversion", f"{m(R5['cc_pre1']['mu'], 3)} ({rng(R5['cc_pre1']['lo'], R5['cc_pre1']['hi'], 3)})", R5['cc_pre1']['k']],
            ["Concordant dating, CCI dose: conversion epoch", f"{m(R5['cc_post']['mu'], 3)} ({rng(R5['cc_post']['lo'], R5['cc_post']['hi'], 3)})", R5['cc_post']['k']],
            ["Concordant dating, CCI dose: net of pre-period", f"{m(R5['cc_net']['mu'], 3)} ({rng(R5['cc_net']['lo'], R5['cc_net']['hi'], 3)})", R5['cc_net']['k']],
            ["Own total effect, benchmark cities", f"{m(R5['sel_pool_in']['mu'])} ({rng(R5['sel_pool_in']['lo'], R5['sel_pool_in']['hi'])})", R5['sel_pool_in']['k']],
            ["Own total effect, other cities", f"{m(R5['sel_pool_out']['mu'])} ({rng(R5['sel_pool_out']['lo'], R5['sel_pool_out']['hi'])})", R5['sel_pool_out']['k']]]
    D.table(['Analysis', 'Estimate, °C per 10 pp (95% CI)', 'Cities'], rows, widths_mm=[85, 45, 16], size=7.5,
            caption=f"**Supplementary Table 16 | Over-adjustment check, CCI-dosed dating and selection of benchmark cities.** CCI-dosed effects are per ten percentage points of CCI urban fraction. Benchmark versus other cities: Mann–Whitney P = {m(R5['sel_p'])}; zones of benchmark cities {R5['sel_zone_in']}, of others {R5['sel_zone_out']}.")
    rows = [[k, m(v['rho'][0]) + f" ({rng(v['rho'][1], v['rho'][2])})", pct(v['tercile'])] for k, v in R5['ext_ccidose'].items() if k != 'n']
    D.table(['Model', 'ρ vs CCI-dosed concordant benchmark', 'Right third'], rows, widths_mm=[50, 50, 25], size=7.5,
            caption=f"**Supplementary Table 17 | Screening against the concordant benchmark with ESA CCI change as the dose** ({R5['ext_ccidose']['n']} city-regions). By world region, Spearman ρ of causal and full models with own effects: " + '; '.join(f"{r} {m(v['causal'])} and {m(v['full'])}" for r, v in R5['rho_by_region'].items()) + '.')
    D.save(f'{OUT}/Supplementary_Information_126_cities_NatSustain.docx')


def source_data():
    with pd.ExcelWriter(f'{OUT}/Source_Data_126_cities_NatSustain.xlsx') as X:
        pd.read_csv(f'{RES}/transfer_nonlinear.csv').to_excel(X, 'Transfer_nonlinear', index=False)
        pd.read_csv(f'{RES}/projection_nonlinear.csv').to_excel(X, 'Fig5_projection_nonlinear', index=False)
        pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city_extra/*.json')]).to_excel(X, 'Fig2_extra_checks', index=False)
        pd.DataFrame([dict(model=k, **{a: (b[0] if isinstance(b, list) else b) for a, b in v.items()}) for k, v in DEC.items()]).to_excel(X, 'Table1_decision', index=False)
        own.reset_index().to_excel(X, 'City_estimates', index=False)
        pd.read_csv(f'{RES}/city_climate.csv').to_excel(X, 'City_climate', index=False)
        pd.read_csv(f'{RES}/backcast_cv.csv').merge(pd.read_csv(f'{RES}/backcast_temporal.csv'), on='city', how='left').to_excel(X, 'Backcast_validation', index=False)
        pd.read_csv(f'{RES}/transfer_change.csv').to_excel(X, 'Fig3_change', index=False)
        pd.read_csv(f'{RES}/conformal.csv').to_excel(X, 'Fig3c_conformal', index=False)
        pd.read_csv(f'{RES}/transfer_intervention.csv').to_excel(X, 'Fig4_intervention', index=False)
        pd.read_csv(f'{RES}/transfer_cityeff.csv').to_excel(X, 'City_transfer', index=False)
        pd.read_csv(f'{RES}/sim_all.csv').to_excel(X, 'Fig5_simulation', index=False)
        pd.read_csv(f'{RES}/projection.csv').to_excel(X, 'Fig6_projection', index=False)
        pd.read_csv(f'{RES}/cmip6_deltas.csv').to_excel(X, 'ED7_cmip6_deltas', index=False)
        pooled = [dict(estimand=k, zone=z, **v) for k, d in S.items() if isinstance(d, dict) and 'All' in d and isinstance(d['All'], dict) and 'mu' in d['All'] for z, v in d.items()]
        pd.DataFrame(pooled).to_excel(X, 'Pooled_estimates', index=False)


if __name__ == '__main__':
    build(); source_data(); print('ok')
