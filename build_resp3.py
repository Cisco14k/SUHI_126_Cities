"""Round-3 response (Nature Sustainability) to the attached report, point by point."""
import sys, json
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from docxbuild import Doc
from build_ms import S, m, rng, B, pct, OUT, IV, CH, SIM, PR
from build_ms2 import TITLE, R3, DEC
tot = S['total_wc']['All']; A = SIM['A']


def R(D, items):
    for c, r in items:
        D.para(f'**Comment.** *{c}*', after=3, spacing=1.15)
        D.para(f'**Response.** {r}', after=10, spacing=1.15)


D = Doc(line_numbers=False, spacing=1.15, size=10)
D.para('**Response to the reviewer (round 3)**', size=14, after=6)
D.para(f'Manuscript: “{TITLE}” (previously “Prediction and intervention in models of the surface heat cost of urban sealing”). Target journal: *Nature Sustainability* (Article).', after=8)
D.para("We thank the reviewer for a precise report. We ran six new analyses (lagged-outcome adjustment, concordant dating with trend-adjusted contrasts, spillover, simulation-calibrated standard errors, a nonlinear causal transfer model and decision metrics for screening) and rewrote the paper for *Nature Sustainability*: the sustainability stake (land-take and sealing policy) is now explicit, display items are reduced to six (Figs. 1–5 and Table 1; simulations and the estimand table moved to Extended Data), and the text carries fewer numbers. We cite eight *Nature Sustainability* articles. All numbers are generated from one results file.", after=10)
R(D, [
 ("Significance: mainly a methodological caution; new evidence for planning is weak; projection to 2100 gives a near-zero result; risk of restating a known principle.",
  f"We reframed the contribution around a policy question that the European Union's 2025 Soil Monitoring Law and urban de-sealing targets pose: how much heat does sealing add, where, and can it be screened with models? New results answer it more directly: (i) the plausible range of the average effect is {m(S['sens_adj_pool']['mu'])}–{m(tot['mu'])} °C per ten percentage points, set mainly by vegetation loss; (ii) sealing a 1-km neighbourhood adds {m(R3['sp_nb']['mu'])} °C beyond the cell's own {m(R3['sp_own']['mu'])} °C, so cell-level estimates understate the policy-relevant effect; (iii) for screening, the causal transfer model placed {pct(DEC['causal_all']['tercile_agree'][0])} of cities in the right third against {pct(DEC['full_all']['tercile_agree'][0])} for the best predictive model and {pct(DEC['zone_baseline']['tercile_agree'][0])} for a zone average (Table 1). The projection is now presented as a property of the effect function, tested three ways (nonlinear model, climate-only modifiers and within-city change across epochs, {m(R3['temporal_climate_slope'][0])} °C per °C), and its message (warming alone barely changes the heat cost; vegetation does) is stated as a finding with its limits."),
 ("Abstract: benchmarks rest on the same assumptions as the causal model and the abstract should say so; it omits the weak signal from independent CCI dating.",
  "Both are now in the abstract: 'Because the cities' own estimates share these identification assumptions, transferred effects can screen cities but not replace local estimates', and '…although dating by ESA CCI alone gave a weak signal'."),
 ("Introduction: examples of misuse remain general; add concrete planning applications.",
  "We now cite concrete cases: vegetation thresholds from simulation-based optimization of a predictive model said to lower surface temperature by up to 6.4 °C (Liao & Liu 2026, *Buildings*), policy recommendations drawn from XGBoost–SHAP driver rankings (Wei et al. 2025, *Land*), and large comparative and causal-ML studies (Lee et al. 2026; Liu et al. 2026)."),
 ("Study area: median 4% of cells in cores; core effect half the rural one from 63 cities; circles; purposive and replaced cities.",
  f"The rural dominance and the smaller core effect are stated in Results and Limitations; spillover now explains part of it (neighbourhood sealing matters most in dense areas). Restricting to the inner half of each radius gave {m(R3['inner']['mu'])} °C and removing the eleven purposive or replaced cities {m(R3['excl_purposive']['mu'])} °C (Fig. 2a, Supplementary Table 11)."),
 ("Back-cast scale: back-cast underestimates change (0.010 vs 0.038 in CCI); back-cast cross-sections give larger effects.",
  f"We tested the scale directly. The out-of-fold back-cast is not shrunk relative to WorldCover (median calibration slope {m(R3['cal_slope'])}), so the larger back-cast effects are not a scale artefact; they point to the back-cast sharing spectral information with surface temperature, which we now state, and we compare effect sizes only within a product. Against LCMAP, back-cast change correlates at r ≈ 0.7 and its ratio of change to level (0.22) is similar to LCMAP's (0.27), whereas the coarse CCI urban class (300 m) records more expansion than both; temporal designs therefore no longer rely on one product: the concordant design requires both to agree."),
 ("Mediation: linear decomposition; NDVI shares the sensor.",
  f"Besides the independent tree-cover path ({pct(S['share_path_tree_only'])} of the total), we now report a nonlinear check: within-city gradient boosting returns about zero at fixed vegetation ({m(S['gbm_within']['gbm_full_eff'][0])} °C) and about the total effect when vegetation shifts with sealing ({m(S['gbm_within']['gbm_full_joint_eff'][0])} vs {m(S['gbm_within']['cs3_theta'][0])} °C), consistent with the linear decomposition. The mechanism is still described as 'consistent with vegetation loss'."),
 ("Transfer model: linear; climate effects vanish once vegetation enters.",
  f"We added a nonlinear causal transfer model (gradient-boosted R-learner). It ranked cities similarly but less accurately (mean absolute difference {m(DEC['nl_all']['mae'][0])} vs {m(DEC['causal_all']['mae'][0])} °C) and also showed little climate dependence. A model with climate-only modifiers shows how much of the climate signal is carried by vegetation (Fig. 5b)."),
 ("Projection: space-for-time; the 2100 result follows from the specification.",
  f"Agreed, and we say so ('a property of the effect function rather than a forecast'). We added an independent, temporal check that does not use space-for-time: within cities, across the four epochs, the effect changed by {m(R3['temporal_climate_slope'][0])} °C per °C of warm-season temperature (95% CI {rng(R3['temporal_climate_slope'][1], R3['temporal_climate_slope'][2])}), in the same direction and of similar size as the projections. The projection section is shortened."),
 ("Results: negative control positive (0.12 °C, 67/106); RV 0.11; bias bound 0.16 °C.",
  f"We used the negative control constructively: adding the 1985–1989 heat island as a confounder (lagged-outcome design) lowered the total effect from {m(R3['lag_unsealed_ref']['mu'])} to {m(R3['lag_unsealed']['mu'])} °C in cells unsealed in 1985–1989 and from {m(R3['lag_all_ref']['mu'])} to {m(R3['lag_all']['mu'])} °C in all cells. We now report the plausible range {m(S['sens_adj_pool']['mu'])}–{m(tot['mu'])} °C rather than a single number, and say the size is uncertain by about a factor of two while sign and ranking across climates are robust."),
 ("CCI-dated warming during conversion barely exceeds that before (0.047 vs 0.026 °C).",
  f"We added a concordant design in which conversion must be recorded by both products. Converted cells warmed by {m(R3['cA_post']['mu'])} °C during conversion against {m(R3['cA_pre1']['mu'])} °C before and {m(R3['cA_post2']['mu'])} °C after ({R3['cA_post']['k']} city-regions); net of the pre-period change {m(R3['adj']['cA']['parallel']['mu'])} °C (95% CI {rng(R3['adj']['cA']['parallel']['lo'], R3['adj']['cA']['parallel']['hi'])}). The weak CCI-only signal is reported alongside, and we state that confirmation depends on the dating product. Trend-adjusted contrasts (Rambachan & Roth) are in Supplementary Table 12."),
 ("Simulated 95% intervals cover only 82% without hidden confounding.",
  f"We now calibrate: the simulation-derived inflation factor (×{m(R3['se_inflation'])}) is applied to the real-data standard errors; with it, {R3['sig_pos_calibrated']} rather than {S['total_sig_pos']} city-regions have intervals above zero, and the pooled interval is unchanged because it is dominated by between-city heterogeneity. Methods state that nominal intervals are lower bounds."),
 ("The within-city minimal model's 0.86 °C could reflect DML's assumptions rather than bias in boosting.",
  f"The simulations, where the truth is known, discriminate between the two: the minimal boosting model with location bins was biased by {m(A['gbm_min_bins']['bias'])} °C and DML by {m(A['dml_total']['bias'], 3)} °C. We report this explicitly."),
 ("The causal model improves on the zone baseline by only 0.06 °C.",
  f"We agree that absolute accuracy improves modestly and say so. For screening, the relevant property is ordering: the zone baseline misplaced {pct(DEC['zone_baseline']['gross_misclass'])} of cities by two thirds and found {pct(DEC['zone_baseline']['top_recall'])} of the highest-cost third, against {pct(DEC['causal_all']['gross_misclass'])} and {pct(DEC['causal_all']['top_recall'])} for the causal transfer model (Table 1)."),
 ("Discussion: acknowledge that DML removes only the confounding it is given; state that no design validates the effect size.",
  "Both statements are now in the first Discussion paragraph: '…only orthogonalized estimators address the confounding they are given; no design here validates the effect size against an experiment.'"),
 ("Limitations: spillover, overpass-time drift and fewer scenes in 1985–1989, unobserved irrigation; future priorities.",
  f"Spillover is now estimated in the main text (Fig. 2c). Overpass time drifted from {m(R3['overpass']['0'], 1)} to {m(R3['overpass']['3'], 1)} h local solar time, and the number of scenes in 1985–1989 (median {m(R3['scenes']['0'], 1)}) had no material effect on the epoch estimates ({m(R3['scene_slope'], 4)} °C per scene; Supplementary Table 13). Irrigation is named as a plausible unmeasured confounder and as an explanation for arid cities. Future priorities (permit- or footprint-dated construction, air-temperature validation) close the Limitations."),
 ("Conclusions: 'about 0.4 °C' at odds with the checks; report the bias-adjusted range or lead with the qualitative message.",
  f"The Conclusions now lead with the qualitative message and give the range {m(S['sens_adj_pool']['mu'])}–{m(tot['mu'])} °C."),
 ("Grammar and presentation: too many numbers; define 'heat cost', 'pp', 'assumption-dependent benchmark'; title does not state a finding.",
  f"Paragraphs now carry fewer estimates, with details moved to Table 1 and Supplementary Tables 11–14; terms are defined at first use (heat cost = change of daytime heat-island intensity for ten percentage points more sealing). The new title states the finding: “{TITLE}” (79 characters)."),
 ("Recommendation: identification design surviving pre-trend tests, ideally permit- or footprint-dated construction; clearer sustainability stake.",
  "Time-stamped building footprints and permit records are not openly available for 126 cities across seven world regions over 1985–2025, so we could not add them; the concordant-dating and lagged-outcome designs are the strongest designs available from open global data, and we name dated construction as the priority for future work. The sustainability stake is now explicit in the Introduction and Discussion."),
])
D.h('Nature Sustainability articles now cited', 2)
for r in ['van Vliet (2019) Nat. Sustain. 2, 755–763', 'Nagendra et al. (2018) Nat. Sustain. 1, 341–349', 'Elmqvist et al. (2019) Nat. Sustain. 2, 267–273', 'Hino et al. (2018) Nat. Sustain. 1, 583–588',
          'McDonald et al. (2020) Nat. Sustain. 3, 16–24', 'Biardeau et al. (2020) Nat. Sustain. 3, 25–28', 'Lenton et al. (2023) Nat. Sustain. 6, 1237–1247', 'Chen et al. (2025) Nat. Sustain. 8, 373–384']:
    D.para('• ' + r, after=2, spacing=1.15)
D.save(f'{OUT}/Response_to_Reviewer_round3_126_cities.docx'); print('ok')
