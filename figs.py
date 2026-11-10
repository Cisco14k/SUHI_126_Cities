"""Main-text figures (Nature Cities style: 183 mm width, Arial-metric type, NPG-based palette)."""
import sys, json, glob, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from figstyle import *
import matplotlib.pyplot as plt, matplotlib as mpl
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
setup()
S = json.load(open(f'{RES}/summary.json'))
ZONES = ['Tropical', 'Arid', 'Temperate', 'Continental']
ZC = dict(ZONE_COL, Polar=NPG['grey']); ZM = dict(ZONE_MK, Polar='v')
MC = {'causal': '#3B5FB0', 'full': '#E64B35', 'partial': '#D9A400', 'minimal': '#00A087', 'full_mono': '#6A51A3',
      'full_loc': '#E64B35', 'minimal_loc': '#00A087', 'full_joint': '#E64B35', 'zone_baseline': '#7F7F7F'}
ML = {'causal': 'Causal transfer', 'full': 'GBM full', 'partial': 'GBM partial', 'minimal': 'GBM minimal', 'full_mono': 'GBM full, monotone',
      'full_loc': 'GBM full + location', 'minimal_loc': 'GBM minimal + location', 'full_joint': 'GBM full, mediators shifted', 'zone_baseline': 'Zone baseline'}
MM_ = {'causal': 'o', 'full': 's', 'partial': 'D', 'minimal': '^', 'full_mono': 'P', 'full_loc': 's', 'minimal_loc': '^', 'full_joint': 'X', 'zone_baseline': 'v'}
OUTF = FIG


def own_df():
    own = pd.DataFrame([json.load(open(f)) for f in glob.glob(f'{RES}/city/*.json')]).set_index('city')
    clim = pd.read_csv(f'{RES}/city_climate.csv').set_index('city')
    return own.join(clim[['zone', 'region', 'lat', 'lon', 'aridity', 'tmax_warm']])


def dotwhisk(ax, y, p, color, marker='o', label=None, ms=4, hollow=False, pi=False):
    if not np.isfinite(p.get('mu', np.nan)): return
    if pi and np.isfinite(p.get('pi_lo', np.nan)):
        ax.plot([p['pi_lo'], p['pi_hi']], [y, y], color=color, lw=3.5, alpha=0.18, solid_capstyle='butt', zorder=1)
    ax.plot([p['lo'], p['hi']], [y, y], color=color, lw=1.1, zorder=2)
    ax.plot(p['mu'], y, marker, ms=ms, mfc='white' if hollow else color, mec=color, mew=0.9, zorder=3, label=label)


def fig1():
    own = own_df(); fig = plt.figure(figsize=(W2, 160 * MM))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.05], width_ratios=[1.4, 1], hspace=0.22, wspace=0.42, left=0.09, right=0.98, top=0.98, bottom=0.12)
    # a: map
    ax = fig.add_subplot(gs[0, :]); import json as js
    land = js.load(open('/home/claude/work/data/ne/land110.geojson'))
    for ft in land['features']:
        geoms = ft['geometry']['coordinates'] if ft['geometry']['type'] == 'MultiPolygon' else [ft['geometry']['coordinates']]
        for poly in geoms:
            xy = np.array(poly[0]); ax.fill(xy[:, 0], xy[:, 1], color='#ECECEC', lw=0.3, ec='#D0D0D0', zorder=0)
    norm = mpl.colors.TwoSlopeNorm(vmin=-0.8, vcenter=0, vmax=1.2)
    for z in ZONES + ['Polar']:
        d = own[own.zone == z]
        sc = ax.scatter(d.lon, d.lat, c=d.cs3_theta, cmap=DIV_CMAP, norm=norm, marker=ZM[z], s=16, ec=INK, lw=0.35, zorder=3, label=z)
    ax.set_xlim(-170, 180); ax.set_ylim(-56, 72); ax.set_aspect('equal'); ax.axis('off')
    cax = ax.inset_axes([0.02, 0.10, 0.16, 0.035]); cb = fig.colorbar(sc, cax=cax, orientation='horizontal'); cb.outline.set_linewidth(0.4)
    cb.set_ticks([-0.8, -0.4, 0, 0.4, 0.8, 1.2]); cb.ax.tick_params(labelsize=5.5, length=1.5)
    cax.set_title('Total effect (°C per 10 pp)', fontsize=6, pad=2, loc='left', fontweight='normal')
    hs = [Line2D([], [], marker=ZM[z], ls='', mfc='white', mec=INK, mew=0.6, ms=4, label=z) for z in ZONES + ['Polar']]
    ax.legend(handles=hs, loc='lower left', bbox_to_anchor=(0.20, 0.03), ncol=5, fontsize=6, handletextpad=0.2, columnspacing=0.8)
    panel(ax, 'a', x=0.0, y=0.98)
    # b: caterpillar of city effects
    ax = fig.add_subplot(gs[1, 0]); d = own.sort_values('cs3_theta').reset_index(); x = np.arange(len(d))
    for z in ZONES + ['Polar']:
        m = d.zone == z
        ax.vlines(x[m], (d.cs3_theta - 1.96 * d.cs3_se)[m], (d.cs3_theta + 1.96 * d.cs3_se)[m], color=ZC[z], lw=0.7)
        ax.plot(x[m], d.cs3_theta[m], ZM[z], ms=2.6, color=ZC[z], mec='white', mew=0.3)
    p = S['total_wc']['All']; ax.axhspan(p['pi_lo'], p['pi_hi'], color=FILL, zorder=0)
    ax.axhline(p['mu'], color=INK, lw=0.7, ls='--'); zero(ax)
    ax.text(len(d) * 0.02, p['mu'] + 0.05, f"pooled {p['mu']:.2f} °C", fontsize=6, color=INK)
    ax.text(len(d) * 0.98, p['pi_lo'] + 0.02, '95% prediction interval', fontsize=5.5, color=INK2, ha='right', va='bottom')
    ax.set_xlim(-2, len(d) + 1); ax.set_xticks([]); ax.set_xlabel(f"{len(d)} city-regions, ranked")
    ax.set_ylabel('Effect of +10 pp impervious cover\non surface heat island (°C)'); panel(ax, 'b', x=-0.16)
    # c: pooled by zone, total / direct / paths
    ax = fig.add_subplot(gs[1, 1]); items = [('total_wc', 'Total', 'o', False, True), ('direct', 'Direct', 's', True, False),
                                             ('path_ndvi', 'Via NDVI', 'D', False, False), ('path_tree_only', 'Via tree cover\n(independent map)', '^', True, False)]
    rows = ['All'] + ZONES; yy = np.arange(len(rows))[::-1] * 1.0
    for j, (k, lab, mk, hol, pi) in enumerate(items):
        for i, r in enumerate(rows):
            dotwhisk(ax, yy[i] + 0.3 - j * 0.2, S[k][r], INK if r == 'All' else ZC[r], mk, hollow=hol, pi=pi and S[k][r]['k'] >= 8, ms=3.4)
    ax.axvline(0, color=INK2, lw=0.5); ax.set_xlim(-1.0, 1.5); ax.set_ylim(-0.6, yy[0] + 0.6)
    ax.set_yticks(yy); ax.set_yticklabels([f"{r}\n(n={S['total_wc'][r]['k']})" for r in rows])
    ax.set_xlabel('°C per 10 pp impervious cover'); ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0)
    hs = [Line2D([], [], marker=mk, ls='', mfc='white' if hol else INK2, mec=INK2, ms=3.6, label=lab) for k, lab, mk, hol, pi in items]
    ax.legend(handles=hs, loc='upper center', bbox_to_anchor=(0.45, -0.13), ncol=2, fontsize=5.8, handletextpad=0.2, columnspacing=0.8)
    ax.text(1.0, 1.0, 'shaded: 95% prediction\ninterval of total (n ≥ 8)', transform=ax.transAxes, ha='right', va='top', fontsize=5.3, color=INK2)
    panel(ax, 'c', x=-0.36)
    save(fig, f'{OUTF}/Fig1.png'); plt.close(fig)


def fig2():
    own = own_df(); R3 = S['r3']
    fig, axs = plt.subplots(2, 2, figsize=(W2, 128 * MM), gridspec_kw=dict(width_ratios=[1.05, 1.1]))
    fig.subplots_adjust(left=0.26, right=0.95, top=0.95, bottom=0.11, wspace=0.75, hspace=0.62); axs = axs.ravel()
    # a: total effect under alternative adjustment sets and samples
    ax = axs[0]
    rows = [(S['total_wc']['All'], 'Main: terrain + location', NPG['navy'], 'o'),
            (S['total_nobins']['All'], 'Terrain only', NPG['grey'], 'o'),
            (R3['lag_unsealed_ref'], 'Cells unsealed in 1985–89', NPG['navy'], 's'),
            (R3['lag_unsealed'], '  + 1985–89 heat island', NPG['red'], 's'),
            (R3['lag_all'], 'All cells + 1985–89 heat island', NPG['red'], 'D'),
            (S['sens_adj_pool'], 'Bias bound (confounder = bins)', NPG['red'], 'X'),
            (R3['inner'], 'Inner half of city-region', NPG['navy'], '^'),
            (R3['excl_purposive'], f"Without {R3['n_excl']} purposive cities", NPG['navy'], 'v')]
    for i_, (p, l, col, mk) in enumerate(rows): dotwhisk(ax, len(rows) - i_, p, col, mk, ms=3.6)
    ax.set_yticks(np.arange(len(rows), 0, -1)); ax.set_yticklabels([l for _, l, _, _ in rows], fontsize=5.8)
    ax.axvline(0, color=INK2, lw=0.5); ax.axvline(S['total_wc']['All']['mu'], color=NPG['navy'], lw=0.5, ls=':')
    ax.set_xlabel('Total effect (°C per 10 pp)'); ax.tick_params(axis='y', length=0); ax.spines['left'].set_visible(False)
    panel(ax, 'a', x=-0.75, y=1.04)
    # b: dated conversions, three dating rules
    ax = axs[1]
    sets = [('cciA', S, 'ESA CCI dating', NPG['green'], 'o'), ('bcA', S, 'Back-cast dating', NPG['purple'], 's'), ('cA', R3, 'Concordant (both)', NPG['red'], 'D')]
    for j_, (d, src, lab, col, mk) in enumerate(sets):
        xs, ys = [], []
        for pn, t in [('pre1', -1), ('post', 0), ('post2', 1)]:
            key = f'{d}_{pn}'; p = (src.get(key, {}).get('All') if src is S else src.get(key))
            if not p or not np.isfinite(p['mu']): continue
            x = t + (j_ - 1) * 0.15; ax.plot([x, x], [p['lo'], p['hi']], color=col, lw=1); ax.plot(x, p['mu'], mk, ms=3.8, color=col, mec='white', mew=0.3, label=lab if pn == 'pre1' else None)
            xs.append(x); ys.append(p['mu'])
        ax.plot(xs, ys, color=col, lw=0.5, alpha=0.6)
    zero(ax); ax.axvline(-0.5, color=INK2, lw=0.5, ls=':')
    ax.set_xticks([-1, 0, 1]); ax.set_xticklabels(['before\n1985–89 to\n1998–02', 'conversion\n1998–02 to\n2012–16', 'after\n2012–16 to\n2021–25'], fontsize=5.6)
    ax.set_ylabel('ΔHI per 10 pp converted (°C)'); ax.legend(loc='upper left', fontsize=5.6, handletextpad=0.2)
    panel(ax, 'b', x=-0.25, y=1.04)
    # c: spillover
    ax = axs[2]
    R4 = S['r4']
    rows = [(R3['sp_own'], 'Own cell (120 m)', NPG['navy'], 'o'), (R3['sp_nb'], '1-km neighbourhood', NPG['red'], 'o'),
            (R4['sp2_own'], 'Own cell, 2-km bins', NPG['navy'], 's'), (R4['sp2_nb'], '1-km neighbourhood, 2-km bins', NPG['red'], 's'),
            (S['total_wc']['All'], 'Own cell, neighbourhood\nnot modelled', NPG['grey'], 'o')]
    for i_, (p, l, col, mk) in enumerate(rows): dotwhisk(ax, len(rows) - i_, p, col, mk, ms=3.8)
    rows = [(p, l) for p, l, _, _ in rows]
    ax.set_yticks(np.arange(len(rows), 0, -1)); ax.set_yticklabels([l for _, l in rows], fontsize=6); ax.axvline(0, color=INK2, lw=0.5)
    ax.set_xlabel('Effect of +10 pp sealing (°C)'); ax.tick_params(axis='y', length=0); ax.spines['left'].set_visible(False); ax.set_ylim(0.4, len(rows) + 0.6)
    panel(ax, 'c', x=-0.75, y=1.04)
    # d: strata and negative control
    ax = axs[3]; rows = [('core', 'Urban core'), ('fringe', 'Fringe'), ('rural', 'Rural'), ('total_wc', 'All cells'), ('nco', 'Negative control\n(1985–89 HI)')]
    for i_, (k, l) in enumerate(rows):
        dotwhisk(ax, len(rows) - i_, S[k]['All'], NPG['navy'] if k != 'nco' else NPG['grey'], 'o' if k != 'nco' else 'X', ms=3.6)
    ax.set_yticks(np.arange(len(rows), 0, -1)); ax.set_yticklabels([f"{l} (n={S[k]['All']['k']})" for k, l in rows], fontsize=6); ax.axvline(0, color=INK2, lw=0.5)
    ax.set_xlabel('°C per 10 pp'); ax.tick_params(axis='y', length=0); ax.spines['left'].set_visible(False); ax.set_ylim(0.4, len(rows) + 0.6)
    panel(ax, 'd', x=-0.62, y=1.04)
    save(fig, f'{OUTF}/Fig2.png'); plt.close(fig)


def fig3():
    fig, axs = plt.subplots(1, 3, figsize=(W2, 70 * MM), gridspec_kw=dict(width_ratios=[1.15, 1.15, 1]))
    fig.subplots_adjust(left=0.07, right=0.99, top=0.9, bottom=0.3, wspace=0.42)
    models = ['causal', 'minimal', 'partial', 'full', 'full_mono']; designs = [('six', 'Six cities out'), ('zone', 'Zone out'), ('continent', 'Continent out')]
    for ai, met in enumerate(['rho', 'slope']):
        ax = axs[ai]
        for j, m in enumerate(models):
            for i, (dn, dl) in enumerate(designs):
                v = S['change'].get(f'{dn}|{m}')
                if not v: continue
                x = i + (j - 2) * 0.15; mu, lo, hi = v[met]
                ax.plot([x, x], [lo, hi], color=MC[m], lw=1); ax.plot(x, mu, MM_[m], ms=3.8, color=MC[m], mec='white', mew=0.3)
        ax.set_xticks(range(3)); ax.set_xticklabels([d for _, d in designs], fontsize=6)
        if met == 'slope': ax.axhline(1, color=INK2, lw=0.6, ls='--'); ax.text(2.5, 1.02, 'ideal', fontsize=5.5, color=INK2, va='bottom', ha='right')
        zero(ax)
        ax.set_ylabel(['Spearman correlation, observed vs\npredicted change 1985–2025', 'Calibration slope'][ai])
        panel(ax, 'ab'[ai], x=-0.25, y=1.03)
    hs = [Line2D([], [], marker=MM_[m], ls='-', lw=0.8, color=MC[m], ms=3.6, label=ML[m]) for m in models]
    axs[0].legend(handles=hs, loc='upper center', bbox_to_anchor=(1.15, -0.13), ncol=5, fontsize=5.8, handletextpad=0.3, columnspacing=0.9)
    ax = axs[2]; K = pd.read_csv(f'{RES}/conformal.csv'); regs = sorted(K.region.unique())
    for j, (m, col) in enumerate([('causal', MC['causal']), ('full', MC['full'])]):
        g = K[K.model == m].groupby('region')
        for i, r in enumerate(regs):
            x = i + (j - 0.5) * 0.3; ax.plot(x, g.cover.median()[r], MM_[m], ms=3.6, color=col, mec='white', mew=0.3)
            cg = g.cover_group.median()[r]
            if np.isfinite(cg):
                ax.plot(x, cg, MM_[m], ms=3.6, mfc='white', mec=col, mew=0.8); ax.plot([x, x], [g.cover.median()[r], cg], color=col, lw=0.5)
    ax.axhline(0.9, color=INK2, lw=0.6, ls='--'); ax.set_ylim(0.6, 1.0)
    ax.set_xticks(range(len(regs))); ax.set_xticklabels([r.replace('C. America & Caribbean', 'C. Am. & Carib.').replace('Northern America', 'N. America').replace('South America', 'S. America') for r in regs], rotation=40, ha='right', fontsize=5.6)
    ax.set_ylabel('Coverage of 90% intervals\nfor single cells'); panel(ax, 'c', x=-0.3, y=1.03)
    hs = [Line2D([], [], marker='o', ls='', color=INK2, ms=3.6, label='all other cities'), Line2D([], [], marker='o', ls='', mfc='white', mec=INK2, ms=3.6, label='same continent')]
    ax.legend(handles=hs, loc='lower left', fontsize=5.5, handletextpad=0.2, title='calibrated on', title_fontsize=5.5)
    save(fig, f'{OUTF}/Fig3.png'); plt.close(fig)


def fig4():
    own = own_df(); I = pd.read_csv(f'{RES}/transfer_intervention.csv').set_index('city').join(own[['cs3_theta', 'cs3_se', 'cs3_direct', 'zone']])
    fig = plt.figure(figsize=(W2, 118 * MM)); gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05], hspace=0.5, wspace=0.38, left=0.08, right=0.99, top=0.92, bottom=0.17)
    lim = [-1.5, 3.0]
    for i, m in enumerate(['causal', 'full', 'minimal']):
        ax = fig.add_subplot(gs[0, i]); col = f'{m}_all'
        for z in ZONES + ['Polar']:
            d = I[I.zone == z]; yv = d[col].clip(lim[0] + 0.04, lim[1] - 0.04)
            ax.errorbar(d.cs3_theta, yv, xerr=1.96 * d.cs3_se, fmt=ZM[z], ms=2.6, color=ZC[z], mec='white', mew=0.3, elinewidth=0.4, capsize=0)
            out = (d[col] < lim[0]) | (d[col] > lim[1])
            ax.plot(d.cs3_theta[out], yv[out], ZM[z], ms=4.2, mfc='none', mec=INK, mew=0.4)
        ax.plot(lim, lim, '--', color=INK2, lw=0.6); zero(ax); ax.axvline(0, color=INK2, lw=0.5)
        ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect('equal')
        v = S['intervention'][col]
        nout = int(((I[col] < lim[0]) | (I[col] > lim[1])).sum())
        if nout: ax.text(0.97, 0.03, f'{nout} beyond axis (ringed)', transform=ax.transAxes, ha='right', fontsize=5.3, color=INK2)
        ax.text(0.03, 0.97, f"{ML[m]}\nMAE {v['mae_total'][0]:.2f} °C\nsign {100 * v['sign'][0]:.0f}%", transform=ax.transAxes, va='top', fontsize=5.8)
        ax.set_xlabel("City's own total effect (°C)")
        if i == 0: ax.set_ylabel('Transferred answer, continent\nheld out (°C per 10 pp)')
        panel(ax, 'abc'[i], x=-0.32 if i == 0 else -0.18, y=1.03)
    hs = [Line2D([], [], marker=ZM[z], ls='', color=ZC[z], ms=3.4, label=z) for z in ZONES + ['Polar']]
    fig.legend(handles=hs, loc='upper center', bbox_to_anchor=(0.53, 1.0), ncol=5, fontsize=5.8, handletextpad=0.2, columnspacing=0.8)
    gsb = gs[1, :].subgridspec(1, 2, width_ratios=[3.3, 1], wspace=0.28); ax = fig.add_subplot(gsb[0])
    entries = [('causal_all', 'causal', 'Causal transfer'), ('minimal_all', 'minimal', 'GBM minimal'), ('minimal_loc_all', 'minimal_loc', 'GBM minimal + location'),
               ('partial_all', 'partial', 'GBM partial'), ('full_all', 'full', 'GBM full'), ('full_loc_all', 'full_loc', 'GBM full + location'),
               ('full_mono_all', 'full_mono', 'GBM full, monotone'), ('full_joint_all', 'full_joint', 'GBM full, shifted'), ('zone_baseline', 'zone_baseline', 'Zone baseline')]
    W_ = S['gbm_within_mae_total']; Wd = S['gbm_within_mae_direct']
    within = [('gbm_min_eff', 'minimal', 'Within-city GBM minimal'), ('gbm_full_eff', 'full', 'Within-city GBM full'), ('gbm_full_joint_eff', 'full_joint', 'Within-city GBM full, shifted')]
    x = 0; ticks = []
    for key, m, lab in entries:
        v = S['intervention'].get(key)
        if not v: continue
        for off, met, hol in [(-0.17, 'mae_total', False), (0.17, 'mae_direct', True)]:
            mu, lo, hi = v[met]; ax.bar(x + off, mu, 0.32, color='white' if hol else MC[m], ec=MC[m], lw=0.8, hatch='////' if hol else None)
            ax.plot([x + off] * 2, [lo, hi], color=INK, lw=0.7)
        ticks.append((x, lab)); x += 1
    x += 0.4
    for key, m, lab in within:
        for off, src, hol in [(-0.17, W_, False), (0.17, Wd, True)]:
            mu, lo, hi = src[key]; ax.bar(x + off, mu, 0.32, color='white' if hol else MC[m], ec=MC[m], lw=0.8, hatch='////' if hol else None, alpha=0.85)
            ax.plot([x + off] * 2, [lo, hi], color=INK, lw=0.7)
        ticks.append((x, lab)); x += 1
    ax.axvline(len(entries) - 0.3, color=INK2, lw=0.5, ls=':')
    ax.text(len(entries) / 2 - 0.5, 1.02, 'pooled models, continent held out', transform=ax.get_xaxis_transform(), ha='center', fontsize=6, color=INK2)
    ax.text(len(entries) + 1.4, 1.02, 'fitted within each city, with location bins', transform=ax.get_xaxis_transform(), ha='center', fontsize=6, color=INK2)
    ax.set_xticks([t for t, _ in ticks]); ax.set_xticklabels([l for _, l in ticks], rotation=35, ha='right', fontsize=5.8)
    ax.set_ylabel('Mean absolute difference from\ncity\'s own estimate (°C)')
    hs = [mpl.patches.Patch(fc=INK2, ec=INK2, label='vs own total effect'), mpl.patches.Patch(fc='white', ec=INK2, hatch='////', label='vs own direct effect')]
    ax.legend(handles=hs, loc='upper right', fontsize=5.8); panel(ax, 'd', x=-0.09, y=1.03)
    ax = fig.add_subplot(gsb[1]); Dm = S['r3']['decision']
    items = [('causal_all', 'causal', 'Causal transfer'), ('full_joint_all', 'full_joint', 'GBM full, shifted'), ('full_all', 'full', 'GBM full'), ('minimal_all', 'minimal', 'GBM minimal'), ('zone_baseline', 'zone_baseline', 'Zone baseline')]
    for i_, (k, mk, lab) in enumerate(items):
        v = Dm[k]['tercile_agree']; y = len(items) - i_
        ax.plot([v[1], v[2]], [y, y], color=MC[mk], lw=1); ax.plot(v[0], y, MM_[mk], ms=3.8, color=MC[mk], mec='white', mew=0.3)
        ax.plot(Dm[k]['top_recall'], y - 0.28, MM_[mk], ms=3.2, mfc='white', mec=MC[mk], mew=0.8)
    ax.axvline(1 / 3, color=INK2, lw=0.5, ls=':'); ax.text(1 / 3, 0.35, 'chance', fontsize=5.3, color=INK2, ha='center')
    ax.set_yticks(np.arange(len(items), 0, -1)); ax.set_yticklabels([l for _, _, l in items], fontsize=5.8); ax.set_xlim(0.2, 0.85); ax.set_ylim(0.2, len(items) + 0.5)
    ax.set_xlabel('Share of cities'); ax.tick_params(axis='y', length=0)
    hs = [Line2D([], [], marker='o', ls='', color=INK2, ms=3.4, label='same tercile'), Line2D([], [], marker='o', ls='', mfc='white', mec=INK2, ms=3.4, label='top third found')]
    ax.legend(handles=hs, loc='lower right', fontsize=5.4, handletextpad=0.2); panel(ax, 'e', x=-0.75, y=1.03)
    save(fig, f'{OUTF}/Fig4.png'); plt.close(fig)


def fig5():
    sim = pd.read_csv(f'{RES}/sim_all.csv'); sc = ['A', 'B03', 'B05', 'B08', 'C']
    scl = {'A': 'A: no unmeasured\nconfounding', 'B03': 'B: unmeasured,\nweak (r = 0.3)', 'B05': 'B: moderate\n(r = 0.5)', 'B08': 'B: strong\n(r = 0.8)', 'C': 'C: nonlinear,\nheterogeneous'}
    ests = [('dml_total', 'true_total', 'DML total', '#3B5FB0', 'o', False), ('gbm_min_bins', 'true_total', 'GBM minimal + bins', '#00A087', '^', False),
            ('gbm_full_bins_joint', 'true_total', 'GBM full, mediators shifted', '#E64B35', 'X', False),
            ('dml_direct', 'true_direct', 'DML direct', '#3B5FB0', 'o', True), ('gbm_full_bins', 'true_direct', 'GBM full + bins', '#E64B35', 's', True)]
    fig, axs = plt.subplots(1, 2, figsize=(W2, 72 * MM), gridspec_kw=dict(width_ratios=[2.2, 1]))
    fig.subplots_adjust(left=0.08, right=0.99, top=0.9, bottom=0.3, wspace=0.3)
    ax = axs[0]
    for j, (e, t, lab, col, mk, hol) in enumerate(ests):
        for i, s in enumerate(sc):
            g = sim[sim.scen == s]; err = (g[e] - g[t]).groupby(g.city).mean()
            x = i + (j - 2) * 0.15; q = err.quantile([0.25, 0.5, 0.75])
            ax.plot([x, x], [q[0.25], q[0.75]], color=col, lw=1.1); ax.plot(x, q[0.5], mk, ms=3.8, mfc='white' if hol else col, mec=col, mew=0.9)
    zero(ax); ax.set_xticks(range(len(sc))); ax.set_xticklabels([scl[s] for s in sc], fontsize=5.8)
    ax.set_ylabel(f'Estimate minus true effect (°C per 10 pp)\nmedian and IQR over {sim.city.nunique()} city-regions')
    hs = [Line2D([], [], marker=mk, ls='', mfc='white' if hol else col, mec=col, ms=3.8, label=lab + (' (vs true direct)' if hol else ' (vs true total)')) for e, t, lab, col, mk, hol in ests]
    ax.legend(handles=hs, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=5.6, handletextpad=0.2, columnspacing=0.8)
    panel(ax, 'a', x=-0.1, y=1.03)
    ax = axs[1]
    for k, (cv, lab, hol) in enumerate([('cover', 'DML total', False), ('cover_dir', 'DML direct', True)]):
        v = [((np.abs(sim[sim.scen == s][('dml_total' if cv == 'cover' else 'dml_direct')] - sim[sim.scen == s][('true_total' if cv == 'cover' else 'true_direct')]) <= 1.96 * sim[sim.scen == s][('dml_total_se' if cv == 'cover' else 'dml_direct_se')]).mean()) for s in sc]
        ax.plot(np.arange(len(sc)) + (k - 0.5) * 0.15, v, 'o-', ms=3.6, lw=0.7, color='#3B5FB0', mfc='white' if hol else '#3B5FB0', label=lab)
    ax.axhline(0.95, color=INK2, lw=0.6, ls='--'); ax.text(1.5, 0.965, 'nominal', fontsize=5.5, color=INK2, ha='right', va='bottom')
    ax.set_ylim(0, 1.02); ax.set_xticks(range(len(sc))); ax.set_xticklabels(['A', 'B weak', 'B mod.', 'B strong', 'C'], fontsize=6)
    ax.set_ylabel('Coverage of 95% confidence intervals'); ax.legend(loc='lower left', fontsize=5.8); panel(ax, 'b', x=-0.3, y=1.03)
    save(fig, f'{OUTF}/ED_Fig9.png'); plt.close(fig)


def fig6():
    P = pd.read_csv(f'{RES}/projection.csv'); fig = plt.figure(figsize=(W2, 105 * MM))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], height_ratios=[1, 0.62], hspace=0.6, wspace=0.32, left=0.08, right=0.99, top=0.95, bottom=0.07)
    ax = fig.add_subplot(gs[0, 0]); cases = [('present', '1991-2020', 'Present', INK2), ('ssp245', '2041-2070', 'SSP2-4.5, 2041–2070', '#9FB0D8'),
                                            ('ssp245', '2071-2100', 'SSP2-4.5, 2071–2100', '#3C5488'), ('ssp585', '2041-2070', 'SSP5-8.5, 2041–2070', '#F3A08F'), ('ssp585', '2071-2100', 'SSP5-8.5, 2071–2100', '#B5281A')]
    for i, z in enumerate(ZONES):
        for j, (sc, pe, lab, col) in enumerate(cases):
            g = P[(P.scen == sc) & (P.period == pe) & (P.zone == z)]
            if not len(g): continue
            cm = g.groupby('model').tau.median() if sc != 'present' else g.tau
            x = i + (j - 2) * 0.15; med = float(np.median(g.groupby('city').tau.median()))
            if sc != 'present': ax.plot([x, x], [cm.min(), cm.max()], color=col, lw=1.2)
            else: ax.plot([x, x], [g.tau_lo.median(), g.tau_hi.median()], color=col, lw=1.2)
            ax.plot(x, med, 'o', ms=3.6, color=col, mec='white', mew=0.3, label=lab if i == 0 else None)
    ax.set_xticks(range(4)); ax.set_xticklabels(ZONES); zero(ax)
    ax.set_ylabel('Heat cost of +10 pp sealing in\nfringe cells (°C; median city)')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=5.6, handletextpad=0.2, columnspacing=0.8); panel(ax, 'a', x=-0.17, y=1.03)
    ax = fig.add_subplot(gs[0, 1]); g = P[(P.scen == 'ssp585') & (P.period == '2071-2100')].groupby('city').agg(d=('d_tau', 'median'), lo=('d_tau', 'min'), hi=('d_tau', 'max'), dT=('dtmax_warm', 'median'), zone=('zone', 'first'), ex=('extrap', 'max'), da=('d_tau_alt', 'median'))
    ax.plot(g.dT, g.da, 'o', ms=2.4, mfc='white', mec=NPG['grey'], mew=0.5, zorder=1, label='climate-only modifiers')
    PN = pd.read_csv(f'{RES}/projection_nonlinear.csv'); PN = PN[(PN.scen == 'ssp585') & (PN.period == '2071-2100')].groupby('city').d_tau_nl.median()
    ax.plot(g.dT, PN.reindex(g.index), '+', ms=3.4, color=NPG['brown'], mew=0.6, zorder=1, label='nonlinear transfer')
    for z in ZONES + ['Polar']:
        d = g[g.zone == z]
        ax.vlines(d.dT, d.lo, d.hi, color=ZC[z], lw=0.4, alpha=0.6); ax.plot(d.dT, d.d, ZM[z], ms=2.8, color=ZC[z], mec='white', mew=0.3, label=z)
        e = d[d.ex > 0]; ax.plot(e.dT, e.d, ZM[z], ms=5, mfc='none', mec=INK, mew=0.4)
    zero(ax); ax.set_xlabel('Δ warm-season Tmax, 2071–2100 vs 1995–2014 (°C)'); ax.set_ylabel('Δ heat cost of sealing (°C)')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=5.5, handletextpad=0.2, columnspacing=0.8)
    tc = S['r3']['temporal_climate_slope']
    panel(ax, 'b', x=-0.2, y=1.03)
    # c: layers schematic
    ax = fig.add_subplot(gs[1, :]); ax.axis('off'); ax.set_xlim(0, 100); ax.set_ylim(0, 30)
    boxes = [(1, 'Prediction layer', 'Where is it hot, how did heat change?\nPredictive models (GBM full) are\nthe better tool (Fig. 3)', '#E8EEF8', '#3B5FB0'),
             (34.5, 'Causal estimand layer', 'What would +10 pp sealing do?\nState the intervention; estimate the total\neffect with confounding adjustment (Figs. 1, 2, 4)', '#E6F5F1', '#00A087'),
             (68, 'Decision layer', 'Which option? Combine effects, their\nuncertainty and other criteria; verify\nlocally with new epochs (Table 1)', '#FBEAE6', '#E64B35')]
    for x0, t, b, fc, ec in boxes:
        ax.add_patch(FancyBboxPatch((x0, 6), 31, 21, boxstyle='round,pad=0.4,rounding_size=1.5', fc=fc, ec=ec, lw=0.8))
        ax.text(x0 + 15.5, 24, t, ha='center', va='center', fontsize=6.6, fontweight='bold', color=ec)
        ax.text(x0 + 15.5, 14.5, b, ha='center', va='center', fontsize=5.7, color=INK, linespacing=1.3)
    for x0 in (32.4, 65.9):
        ax.annotate('', xy=(x0 + 2.2, 16.5), xytext=(x0, 16.5), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=0.7))
    ax.text(50, 1.5, 'Caveats: daytime clear-sky surface temperature only; screening, not design; transferred effects rank cities but do not replace local estimates;\n'
            'projections hold the surface fixed and assume the present climate–effect relation holds under future climates.', ha='center', va='center', fontsize=5.4, color=INK2)
    panel(ax, 'c', x=-0.02, y=0.98)
    save(fig, f'{OUTF}/Fig5.png'); plt.close(fig)


if __name__ == '__main__':
    import os; os.makedirs(OUTF, exist_ok=True)
    for f in (sys.argv[1:] or ['fig1', 'fig2', 'fig3', 'fig4', 'fig5', 'fig6']):
        globals()[f](); print(f, flush=True)
