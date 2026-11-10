"""Extended Data figures."""
import sys, json, glob, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from figstyle import *
import matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from scipy.stats import spearmanr
from figs import own_df, ZC, ZM, ZONES, MC, ML, MM_, S, dotwhisk
setup()


def ed1():
    fig, ax = plt.subplots(figsize=(W2, 95 * MM)); ax.axis('off'); ax.set_xlim(0, 100); ax.set_ylim(0, 60)
    col = [('Data, 1985–2025', '#E8EEF8', '#3B5FB0', ['Landsat C2 L2, 4 warm-season epochs', '(1985–89, 1998–2002, 2012–16, 2021–25)', 'ESA WorldCover 2021; Copernicus DEM', 'ESA CCI land cover; LCMAP (US)', 'TerraClimate 1991–2020', 'NEX-GDDP-CMIP6 (5 GCMs, 2 SSPs)']),
           ('Surface state', '#E6F5F1', '#00A087', ['Median composites, observed only', 'OLI-harmonized reflectance, NDVI, albedo', 'Elevation-adjusted LST; heat island HI', 'Impervious & tree cover back-cast', '(city-specific, block CV)', 'Validated vs CCI and LCMAP']),
           ('Within-city estimands', '#FFF6DC', '#B38600', ['DML total effect (terrain + location)', 'Direct effect and mediation paths', 'Epochs, first differences, strata', 'Dated conversion (CCI, back-cast)', 'Negative control; sensitivity (RV)', 'Within-city GBM comparison']),
           ('Transfer and use', '#FBEAE6', '#E64B35', ['Causal transfer model vs pooled GBM', 'Change 1985–2025; intervention +10 pp', 'Six-, zone-, continent-out; bootstrap', 'Conformal intervals (global, continent)', 'Simulations: assumption checks', 'CMIP6 screening to 2100'])]
    for i, (t, fc, ec, items) in enumerate(col):
        x0 = 1 + i * 25; ax.add_patch(FancyBboxPatch((x0, 3), 22.5, 53, boxstyle='round,pad=0.3,rounding_size=1.2', fc=fc, ec=ec, lw=0.8))
        ax.text(x0 + 11.25, 52, t, ha='center', fontsize=7, fontweight='bold', color=ec)
        for j, it in enumerate(items): ax.text(x0 + 11.25, 45 - j * 7, it, ha='center', va='center', fontsize=5.8, color=INK)
        if i < 3: ax.annotate('', xy=(x0 + 24.6, 30), xytext=(x0 + 23.1, 30), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=0.7))
    save(fig, f'{FIG}/ED_Fig1.png'); plt.close(fig)


def ed2():
    own = own_df(); bc = pd.read_csv(f'{RES}/backcast_cv.csv').set_index('city').join(own[['zone']]); bt = pd.read_csv(f'{RES}/backcast_temporal.csv').set_index('city')
    sc = pd.concat([pd.read_csv(f).assign(city=f.split('/')[-1][:-11]) for f in glob.glob(f'{DATA}/landsat/*_scenes.csv')])
    fig, axs = plt.subplots(1, 4, figsize=(W2, 62 * MM)); fig.subplots_adjust(left=0.07, right=0.99, top=0.9, bottom=0.3, wspace=0.55)
    ax = axs[0]; n = sc[sc.ok].groupby(['city', 'epoch']).size().unstack()
    ax.boxplot([n[k].dropna() for k in range(4)], widths=0.5, medianprops=dict(color=NPG['red']), flierprops=dict(ms=2), boxprops=dict(lw=0.6), whiskerprops=dict(lw=0.6), capprops=dict(lw=0.6))
    ax.set_xticklabels(['1985–89', '1998–02', '2012–16', '2021–25'], rotation=35, ha='right', fontsize=6); ax.set_ylabel('Usable scenes per city-region'); panel(ax, 'a', x=-0.35)
    ax = axs[1]
    for j, (k, lab) in enumerate([('isa_r2', 'Impervious'), ('tree_r2', 'Tree cover')]):
        for z in ZONES + ['Polar']:
            v = bc[bc.zone == z][k]; ax.plot(np.full(len(v), j) + np.random.default_rng(1).uniform(-0.18, 0.18, len(v)), v, ZM[z], ms=2.4, color=ZC[z], mec='white', mew=0.2)
        ax.plot([j - 0.25, j + 0.25], [bc[k].median()] * 2, color=INK, lw=1)
    ax.set_xticks([0, 1]); ax.set_xticklabels(['Impervious', 'Tree cover']); ax.set_xlim(-0.5, 1.5); ax.set_ylim(0, 1); ax.set_ylabel('Spatial-block CV R², 2021–2025'); panel(ax, 'b', x=-0.35)
    ax = axs[2]; ks = [('cci_lev0', 'L 1985–89'), ('cci_lev1', 'L 1998–02'), ('cci_lev2', 'L 2012–16'), ('cci_chg13', 'Δ 2000–20'), ('cci_chg03', 'Δ 1992–20')]
    for j, (k, lab) in enumerate(ks):
        v = bt[k].dropna(); ax.plot(np.full(len(v), j) + np.random.default_rng(2).uniform(-0.18, 0.18, len(v)), v, 'o', ms=1.8, color=NPG['green'], alpha=0.6, mec='none')
        ax.plot([j - 0.25, j + 0.25], [v.median()] * 2, color=INK, lw=1)
    ax.set_xticks(range(len(ks))); ax.set_xticklabels([l for _, l in ks], fontsize=5.6, rotation=40, ha='right'); ax.set_ylim(-0.5, 1); zero(ax)
    ax.set_ylabel('Pearson r with ESA CCI urban\n(1.2-km blocks)'); panel(ax, 'c', x=-0.35)
    ax = axs[3]; ks = [('lc_lev0', 'L 1985–89'), ('lc_lev1', 'L 1998–02'), ('lc_lev2', 'L 2012–16'), ('lc_chg03', 'Δ 1987–21'), ('lc_chg13', 'Δ 2000–21')]
    for j, (k, lab) in enumerate(ks):
        if k not in bt: continue
        v = bt[k].dropna(); ax.plot(np.full(len(v), j) + np.random.default_rng(3).uniform(-0.18, 0.18, len(v)), v, 's', ms=2.4, color=NPG['purple'], mec='white', mew=0.2)
        ax.plot([j - 0.25, j + 0.25], [v.median()] * 2, color=INK, lw=1)
    ax.set_xticks(range(len(ks))); ax.set_xticklabels([l for _, l in ks], fontsize=5.6, rotation=40, ha='right'); ax.set_ylim(-0.5, 1); zero(ax)
    ax.set_ylabel('Pearson r with LCMAP developed\n(US city-regions)'); panel(ax, 'd', x=-0.35)
    save(fig, f'{FIG}/ED_Fig2.png'); plt.close(fig)


def scat(ax, own, x, y, xl, yl, xe=None, lim=None):
    for z in ZONES + ['Polar']:
        d = own[own.zone == z].dropna(subset=[x, y])
        if xe: ax.errorbar(d[x], d[y], xerr=1.96 * d[xe], fmt=ZM[z], ms=2.4, color=ZC[z], mec='white', mew=0.2, elinewidth=0.3)
        else: ax.plot(d[x], d[y], ZM[z], ms=2.6, color=ZC[z], mec='white', mew=0.2)
    d = own.dropna(subset=[x, y]); lim = lim or [min(d[x].min(), d[y].min()) - 0.05, max(d[x].max(), d[y].max()) + 0.05]
    ax.plot(lim, lim, '--', color=INK2, lw=0.6); ax.set_xlim(lim); ax.set_ylim(lim); zero(ax); ax.axvline(0, color=INK2, lw=0.5)
    r = spearmanr(d[x], d[y]).correlation; ax.text(0.04, 0.96, f'Spearman {r:.2f}\nn = {len(d)}', transform=ax.transAxes, va='top', fontsize=5.6)
    ax.set_xlabel(xl); ax.set_ylabel(yl)


def ed3():
    own = own_df(); fig, axs = plt.subplots(1, 4, figsize=(W2, 52 * MM)); fig.subplots_adjust(left=0.07, right=0.99, top=0.86, bottom=0.22, wspace=0.55)
    scat(axs[0], own, 'cs3_theta', 'bc3_theta', 'Total, WorldCover ISA (°C)', 'Total, back-cast ISA (°C)')
    scat(axs[1], own, 'bc3_theta', 'bc0_theta', 'Back-cast, 2021–25 (°C)', 'Back-cast, 1985–89 (°C)')
    scat(axs[2], own, 'cs3_theta', 'fd03_theta', 'Cross-section 2021–25 (°C)', 'First difference 1985–2025 (°C)')
    scat(axs[3], own, 'cs3_theta', 'cs3_theta_nobins', 'Terrain + location bins (°C)', 'Terrain only (°C)')
    for i, a in enumerate(axs): panel(a, 'abcd'[i], x=-0.4)
    hs = [Line2D([], [], marker=ZM[z], ls='', color=ZC[z], ms=3.4, label=z) for z in ZONES + ['Polar']]
    fig.legend(handles=hs, loc='upper center', ncol=5, fontsize=6, bbox_to_anchor=(0.5, 1.0))
    save(fig, f'{FIG}/ED_Fig3.png'); plt.close(fig)


def ed4():
    own = own_df(); fig, axs = plt.subplots(1, 4, figsize=(W2, 52 * MM)); fig.subplots_adjust(left=0.07, right=0.99, top=0.86, bottom=0.22, wspace=0.5)
    ax = axs[0]; ax.hist(own.cs3_r2_DW.dropna(), bins=20, color=NPG['navy'], ec='white', lw=0.3); ax.set_xlabel('Share of ISA variance explained\nby terrain and location (R²)'); ax.set_ylabel('City-regions')
    ax.axvline(own.cs3_r2_DW.median(), color=NPG['red'], lw=0.8); panel(ax, 'a', x=-0.3)
    ax = axs[1]; ax.hist(own.sens_rv.dropna(), bins=20, color=NPG['navy'], ec='white', lw=0.3)
    ax.hist(own.sens_r2dz_bins.dropna(), bins=20, histtype='step', color=NPG['red'], lw=0.8)
    ax.set_xlabel('Robustness value (filled) and\nlocation-bin partial R² with ISA (line)'); panel(ax, 'b', x=-0.3)
    ax = axs[2]; scat(ax, own, 'cs3_theta', 'nco_theta', 'Total effect, 2021–25 (°C)', 'Negative control: same ISA\non 1985–89 HI (°C)'); panel(ax, 'c', x=-0.4)
    ax = axs[3]; scat(ax, own, 'cs3_theta', 'cs3_direct', 'Total effect (°C)', 'Direct effect (°C)'); panel(ax, 'd', x=-0.4)
    save(fig, f'{FIG}/ED_Fig4.png'); plt.close(fig)


def ed5():
    T = pd.read_csv(f'{RES}/transfer_change.csv'); clim = pd.read_csv(f'{RES}/city_climate.csv').set_index('city')
    T = T[T.design == 'six'].join(clim[['zone', 'region']], on='city'); models = ['causal', 'minimal', 'partial', 'full', 'full_mono']
    fig, axs = plt.subplots(1, 2, figsize=(W2, 60 * MM), gridspec_kw=dict(width_ratios=[1, 1.5])); fig.subplots_adjust(left=0.07, right=0.99, top=0.9, bottom=0.32, wspace=0.25)
    for ai, (col, cats) in enumerate([('zone', ZONES), ('region', sorted(T.region.unique()))]):
        ax = axs[ai]
        for j, m in enumerate(models):
            g = T[T.model == m].groupby(col).rho.median()
            ax.plot(np.arange(len(cats)) + (j - 2) * 0.14, [g.get(c, np.nan) for c in cats], MM_[m], ms=3.6, color=MC[m], mec='white', mew=0.3, ls='', label=ML[m])
        ax.set_xticks(range(len(cats))); ax.set_xticklabels([c.replace('C. America & Caribbean', 'C. Am. & Carib.') for c in cats], rotation=30, ha='right', fontsize=6)
        zero(ax); ax.set_ylabel('Median Spearman correlation'); panel(ax, 'ab'[ai], x=-0.14 if ai else -0.2)
    axs[1].legend(loc='upper center', bbox_to_anchor=(0.3, -0.35), ncol=5, fontsize=5.8, handletextpad=0.2)
    save(fig, f'{FIG}/ED_Fig5.png'); plt.close(fig)


def ed6():
    own = own_df(); fig, axs = plt.subplots(1, 3, figsize=(W2, 60 * MM)); fig.subplots_adjust(left=0.07, right=0.99, top=0.88, bottom=0.2, wspace=0.42)
    scat(axs[0], own, 'cs3_theta', 'gbm_min_eff', 'DML total effect (°C)', 'Within-city GBM minimal (°C)')
    scat(axs[1], own, 'cs3_direct', 'gbm_full_eff', 'DML direct effect (°C)', 'Within-city GBM full (°C)')
    scat(axs[2], own, 'cs3_theta', 'gbm_full_joint_eff', 'DML total effect (°C)', 'Within-city GBM full,\nmediators shifted (°C)')
    for i, a in enumerate(axs): panel(a, 'abc'[i], x=-0.3)
    save(fig, f'{FIG}/ED_Fig6.png'); plt.close(fig)


def ed7():
    D = pd.read_csv(f'{RES}/cmip6_deltas.csv'); clim = pd.read_csv(f'{RES}/city_climate.csv').set_index('city'); D = D.join(clim[['zone']], on='city')
    fig, axs = plt.subplots(1, 3, figsize=(W2, 58 * MM)); fig.subplots_adjust(left=0.09, right=0.99, top=0.88, bottom=0.28, wspace=0.42)
    cases = [('ssp245', '2041-2070', '#9FB0D8'), ('ssp245', '2071-2100', '#3C5488'), ('ssp585', '2041-2070', '#F3A08F'), ('ssp585', '2071-2100', '#B5281A')]
    for ai, (v, lab) in enumerate([('dtmax_warm', 'Δ warm-season Tmax (°C)'), ('rppt', 'Precipitation ratio'), ('aridity_f', 'Future aridity / present')]):
        ax = axs[ai]
        for j, (sc, pe, col) in enumerate(cases):
            for i, z in enumerate(ZONES):
                g = D[(D.scen == sc) & (D.period == pe) & (D.zone == z)]
                val = g[v] if v != 'aridity_f' else g.aridity_f / g.aridity
                q = val.quantile([0.1, 0.5, 0.9]); x = i + (j - 1.5) * 0.17
                ax.plot([x, x], [q[0.1], q[0.9]], color=col, lw=1); ax.plot(x, q[0.5], 'o', ms=3.2, color=col, mec='white', mew=0.3, label=f"{sc.upper().replace('SSP245', 'SSP2-4.5').replace('SSP585', 'SSP5-8.5')}, {pe.replace('-', '–')}" if i == 0 else None)
        ax.set_xticks(range(4)); ax.set_xticklabels(ZONES, rotation=25, ha='right', fontsize=6); ax.set_ylabel(lab); panel(ax, 'abc'[ai], x=-0.3)
        if v != 'dtmax_warm': ax.axhline(1, color=INK2, lw=0.5)
    axs[0].legend(loc='upper center', bbox_to_anchor=(1.7, -0.3), ncol=4, fontsize=5.8)
    save(fig, f'{FIG}/ED_Fig7.png'); plt.close(fig)


def ed8(cities=('Kolkata', 'Lahore', 'Chengdu', 'Kyiv')):
    import transfer as T
    I = T.build(); H, Rz = I['H'], I['R']; causal = T.Causal().fit(Rz[~Rz.city.isin(cities)])
    fig, axs = plt.subplots(len(cities), 3, figsize=(W2, 52 * MM * len(cities) / 1.6)); fig.subplots_adjust(left=0.08, right=0.92, top=0.93, bottom=0.07, wspace=0.08, hspace=0.12)
    specs = [('hi3', 'Heat island, 2021–25 (°C)', DIV_CMAP, (-6, 6)), ('dhi', 'Change of HI, 1985–89 → 2021–25 (°C)', DIV_CMAP, (-4, 4)), ('tau', 'Heat cost of +10 pp sealing,\ntransferred (°C)', DIV_CMAP, (-1, 1))]
    for i, c in enumerate(cities):
        h = H[H.city == c].copy()
        if not len(h): continue
        h['dhi'] = h.hi3 - h.hi0; h['tau'] = causal.tau(T.vmat(h, h.wc_tree.values, h.wc_built.values))
        h['bx'] = np.floor(h.dx / 1.2) * 1.2 + 0.6; h['by'] = np.floor(h.dy / 1.2) * 1.2 + 0.6
        B = h.groupby(['bx', 'by'])[['hi3', 'dhi', 'tau']].mean().reset_index()
        for j, (v, lab, cm, (lo, hi)) in enumerate(specs):
            ax = axs[i, j]; s = ax.scatter(B.bx, B.by, c=B[v], cmap=cm, vmin=lo, vmax=hi, s=1.6, marker='s', lw=0)
            ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([]); [sp.set_visible(False) for sp in ax.spines.values()]
            if i == 0: ax.set_title(lab, fontsize=6.5, loc='center')
            if j == 0: ax.set_ylabel(c, fontsize=7)
            if i == len(cities) - 1:
                cax = ax.inset_axes([0.15, -0.1, 0.7, 0.04]); cb = fig.colorbar(s, cax=cax, orientation='horizontal'); cb.ax.tick_params(labelsize=5.5, length=1.5); cb.outline.set_linewidth(0.3)
    save(fig, f'{FIG}/ED_Fig8.png'); plt.close(fig)


if __name__ == '__main__':
    for f in (sys.argv[1:] or ['ed1', 'ed2', 'ed3', 'ed4', 'ed5', 'ed6', 'ed7', 'ed8']):
        globals()[f](); print(f, flush=True)
