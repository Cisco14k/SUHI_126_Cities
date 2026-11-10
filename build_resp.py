"""Point-by-point response to Reviewers A and B, the co-author comments and the tracked-change comments."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from docxbuild import Doc
from build_ms import S, m, rng, B, pct, E, MU, OUT, TITLE, IV, CH, SIM, PR
tot = S['total_wc']['All']
_o = json.load(open(f'{OUT}/ref_order.json'))['order']; REFN = ', '.join(str(_o.index(k) + 1) for k in ['logan2020', 'lundberg2020', 'reichstein2019', 'liu2026'])


def R(D, items):
    for c, r in items:
        D.para(f'**Comment.** *{c}*', after=3, spacing=1.15)
        D.para(f'**Response.** {r}', after=10, spacing=1.15)


def build():
    D = Doc(line_numbers=False, spacing=1.15, size=10)
    D.para('**Response to the reviewers**', size=14, after=6)
    D.para(f'Manuscript: “{TITLE}” (revised; previously “Predictive skill does not imply correct intervention effects in urban heat models”). Target journal: *Nature Cities*.', after=10)
    D.h('Summary of the revision', 2)
    summ = [
        "We re-ran the full pipeline for 1985–2025 with four epochs labelled by year ranges (1985–1989, 1998–2002, 2012–2016, 2021–2025), downloading Landsat Collection 2 composites anew for all 126 city-regions. Composites now use observed values only; the gap-filling model of the previous version, which reviewers noted could reproduce assumed land-cover relationships, has been removed.",
        "The roughness analyses and the 2030 growth scenarios, which depended on modelled building heights and on GHSL trend extrapolations, have been removed. The paper now concerns sealing estimands only, which removes the shadow and view-geometry concern about roughness, the upward-versus-outward growth claims and the missing uncertainty propagation in the growth numbers.",
        "New identification checks: dated-conversion (event-study-style) designs with conversion dated by the independent ESA CCI land-cover product and by our back-cast, a negative-control outcome, Cinelli–Hazlett sensitivity bounds benchmarked on the location bins, overlap diagnostics, and estimates for urban cores, fringes and rural land separately.",
        "Independent temporal validation of the back-cast against ESA CCI (global) and LCMAP (12 US city-regions).",
        "A fair comparison: gradient boosting fitted within each city with the same location bins and folds as DML, in the data and in the simulations.",
        "Transfer results now carry 95% bootstrap intervals over cities for all metrics, include a zone baseline and group-conditional (continent) conformal intervals, and avoid claims of general superiority.",
        "Simulations are repeated (five replicates × 60 city-regions × five scenarios), define the vegetation response explicitly, vary the strength of unmeasured confounding (weak, moderate, strong) and report interval coverage; they are presented as assumption checks after the transfer results.",
        "New: CMIP6 (NEX-GDDP, five GCMs, SSP2-4.5 and SSP5-8.5) screening of how the transferred heat cost of sealing would change under climates of 2041–2070 and 2071–2100. CMIP7 projections are not yet publicly available as downscaled daily fields, so CMIP6 was used.",
        "Reframed for *Nature Cities*: the contribution is stated as an estimand comparison and transfer test across continents, not a decision analysis; prediction, causal-estimand and decision layers are separated (Table 1, Fig. 6c); SDG linkage removed; Data and Code availability statements added; all numbers in text, tables and figures are generated from one results file.",
    ]
    for s in summ: D.para('• ' + s, after=3, spacing=1.15)
    D.para(f"Headline numbers changed with the new data and design. The pooled total effect of ten percentage points of sealing is now {E('total_wc')} (previously 0.41 °C), the median own effect {m(S['median_total'])} °C, the direct effect {E('direct')}. In the continent-out intervention test the causal transfer model answered {m(IV['causal_all']['median'][0])} °C, the full GBM {m(IV['full_all']['median'][0])} °C and the minimal GBM {m(IV['minimal_all']['median'][0])} °C. We report these and all comparisons with uncertainty.", after=10)

    D.h('Reviewer A', 2)
    R(D, [
     ("Abstract: reports 0.41 °C (pooled) and implicitly 0.43 °C (median) without saying which is which; 'came closer' at 0.51 °C without the target; omits the failed pre-trend test and the confounder simulation.",
      f"The abstract now names the pooled total effect as the reference ({m(tot['mu'])} °C), states the restricted model's answer ({m(IV['minimal_all']['median'][0])} °C) without implying it is correct, and reports that dated conversions showed no consistent pre-trends while the negative control and sensitivity bounds leave unmeasured confounding plausible."),
     ("Introduction overstates the gap; the novelty lies in scale, cross-city transfer and the urban application. Align the growth-form motivation with its later status.",
      "The Introduction now states that the mediator problem is established and that the contribution is an estimand comparison and transfer test across continents (final paragraph). The growth-form question has been removed together with the roughness and 2030 analyses."),
     ("Rural-dominated sample; developed-cell check should be more prominent.",
      f"Effects are now estimated separately for urban cores, fringes and rural land and shown in Fig. 2d and the Results: {E('core')} in cores, {E('fringe')} at fringes, {E('rural')} in rural land. The Limitations name the rural dominance explicitly."),
     ("Cities included 'to connect with earlier work of ours' compromises double-blind review; companion analyses may raise overlap concerns.",
      "The wording is removed. Supplementary Note 1 now describes the eight cities as a pre-specified list of rapidly growing cities in two countries, and the companion-analysis statement has been removed from the manuscript; the analyses reported here (1985–2025 composites, estimand comparisons, transfer and simulations) are new to this paper. We will describe any related submissions in the cover letter to the editor, as Nature Portfolio policy requires."),
     ("Unequal comparison: GBM pooled across cities while DML uses within-city location bins. A within-city GBM is needed.",
      f"Added in the data (Fig. 4d, Extended Data Fig. 6) and in the simulations (Fig. 5). Within cities, with identical features, bins and folds, the minimal GBM implied a median {m(S['gbm_within']['gbm_min_eff'][0])} °C against a DML total of {m(S['gbm_within']['cs3_theta'][0])} °C, and the full GBM {m(S['gbm_within']['gbm_full_eff'][0])} °C against a DML direct effect of {m(S['gbm_within']['cs3_direct'][0])} °C. The conditioning set therefore decides the contrast even with matched information."),
     ("Circular benchmark: models judged against the cities' own DML estimates; simulations match DML's partially linear assumptions.",
      "We now say explicitly in Results, Fig. 4 legend and Table 2 that the own estimates are assumption-dependent benchmarks, and that the simulations check assumptions rather than validate the estimates (section moved after the transfer results; Fig. 5 legend). Scenario C departs from the partially linear structure."),
     ("Roughness effect may reflect shadows and view geometry.",
      "The roughness analyses have been removed; the paper concerns sealing only."),
     ("Mediation through NDVI rests on the same sensor; only ~38% is confirmed with independent tree cover.",
      f"We now describe the mechanism as consistent with vegetation loss rather than established, report the independent tree-cover path ({E('path_tree_only')}, {pct(S['share_path_tree_only'])} of the total) in Fig. 1c, and state the assumptions of the linear decomposition in Methods and Supplementary Note 2."),
     ("Results: DiD fails parallel trends; unmeasured-confounder simulation shows large bias; transferred effects within own CI in only 18%.",
      f"The dated-conversion designs, the negative control and the sensitivity bounds are now a dedicated Results section and Fig. 2. Bias under unmeasured confounding is reported at three strengths, with interval coverage. The share of transferred effects inside the city's own interval is {pct(S['city_interval']['within_own_ci'])} and is stated in Results."),
     ("Sign conventions inconsistent.", "With roughness removed, all effects are warming per ten percentage points of sealing (°C), negative values indicating cooling; the convention is stated in Methods."),
     ("2030 growth numbers should be less prominent.", "Removed."),
     ("Complementarity claim needs nuance: the causal model is poor for single cells.", f"The Discussion now assigns prediction to predictive models and states that the causal transfer model is not a prediction tool (single-cell intervals {m(S['conformal']['causal']['q90'], 1)} °C half-width)."),
     ("'Avoiding sealing is more effective than compensating through roughness' goes too far.", "Removed with the roughness analyses."),
     ("Limitations missing: shadows/view angle, rural dominance, non-independence of cities in conformal intervals.",
      "Rural dominance and non-independence are now in Limitations; group-conditional (same-continent) conformal intervals are reported in Fig. 3c and Supplementary Table 5. Shadows no longer apply."),
     ("Conclusions: 'about 0.4 °C' sits awkwardly with confounding and heterogeneity; lead with the estimand message.",
      "The Conclusions now lead with the estimand message, call the numbers conditional causal estimates and give them by zone."),
     ("Presentation: Supplementary Table 6 caption leftover; harmonize time period; spell out abbreviations; remove identifying wording; title.",
      f"Fixed. Periods are 1985–2025 throughout with epochs as year ranges; ISA and HI are defined at first use; the title is now “{TITLE}”, without an active verb and within 90 characters, naming the planning stake."),
    ])
    D.h('Reviewer B', 2)
    R(D, [
     ("Abstract presents vegetation loss as established and attributes the full model's small estimate too confidently to holding vegetation fixed; state model-implied contrasts and conditional estimates; acknowledge lack of quasi-experimental validation; distinguish point estimates from uncertainty.",
      "Revised accordingly: 'mostly through lower vegetation' is stated as an estimate, the full model's answer is described as 'a model-implied contrast at fixed vegetation', the estimates are 'under stated identification assumptions', and the checks are summarized. The simulation section distinguishes point recovery from interval coverage."),
     ("Introduction: give examples of misuse of predictive perturbations; distinguish intervention definition from estimator; explain the planning advance.",
      f"Examples of predictive importance or partial dependence read as mitigation potential are cited (refs {REFN}), and the paragraph ends with 'The problem lies in the estimand, not in the algorithm: gradient boosting is also the workhorse inside DML.' The within-city GBM comparison makes this distinction empirical."),
     ("Rural-dominated sample; present core, fringe and rural estimates and assess transportability; implications of purposive selection and replacements.",
      "Core, fringe and rural estimates are in Fig. 2d and Results; transportability is discussed in Methods and Limitations with references to transport and area-of-applicability; Supplementary Note 1 discusses purposive inclusion and replacements."),
     ("Identification: terrain and location may miss irrigation, management, socioeconomic and redevelopment processes; independent temporal validation of land cover; gap-filling predictors and observed-only analyses; overlap.",
      f"(i) Negative-control outcome, dated conversion with independent dating and sensitivity bounds were added (Fig. 2). (ii) The back-cast is validated against ESA CCI and LCMAP (Extended Data Fig. 2, Supplementary Table 9). (iii) Gap filling has been removed; all composites are observed-only. (iv) Overlap is described by the residual variance of sealing (median {pct(1 - S['overlap_r2_DW_median'])} left after adjustment) and by the location-bin benchmark; we do not claim that this proves overlap."),
     ("Simulation coverage under-calibrated (85%/80% in A; 77%/60% in C); investigate with repeated simulations and calibration.",
      (f"Repeated simulations now report coverage per scenario: {pct(SIM['A']['cover_total'])} (total) and {pct(SIM['A']['cover_direct'])} (direct) without unmeasured confounding, and {pct(SIM['C']['cover_total'])} under nonlinear effects; under unmeasured confounding coverage collapses. We state that nominal intervals are reliable only when the assumptions hold." if SIM else "See Fig. 5.")),
     ("Continent-out error improves only modestly over the zone baseline (0.25 vs 0.28 °C) with lower sign agreement; report uncertainty and avoid claims of superiority.",
      f"All metrics now carry bootstrap intervals (Table 2). The causal transfer model's mean absolute difference was {B(IV['causal_all']['mae_total'])} °C against {B(IV['zone_baseline']['mae_total'])} °C for the zone baseline; we describe the improvement as modest and the advantage as lying mainly in ranking."),
     ("Discussion overstates: agreement with an assumption-dependent benchmark; matched estimands, training information and tuning; growth result conditional.",
      "Model comparisons now include matched within-city fits; pooled models share training cities and fixed hyperparameters; benchmark language revised throughout; the growth result has been removed."),
     ("Limitations: priorities include dated conversion events, validated historical land cover, repeated simulations, air-temperature observations; define the vegetation response under intervention in the simulation.",
      "Dated conversion, validated back-cast and repeated simulations are now done; the simulation defines NDVI = h(W) + a_c·ISA + u explicitly (Methods); air-temperature validation remains a stated priority."),
     ("Conclusions: replace 'recovered by causal designs'; separate overall from non-arid effects; do not present the prediction interval as an observed range; emphasize screening and local validation.",
      "Revised as requested; the prediction interval is described as an interval for a new city-region."),
     ("Terminology: 'total effect' at fixed roughness; c. 2013 vs c. 2014; built volume vs floor area; 'whatever its accuracy'; Data and Code availability.",
      "Roughness and growth are removed, so the total effect is now the effect at fixed terrain and location only, consistently in figures and Methods; epochs are year ranges; the qualifier is removed; Data and Code availability statements and Supplementary Software are provided."),
    ])
    D.h('Co-author comments (My comments or suggestions)', 2)
    R(D, [
     ("Sharpen the contribution linked to the large-scale transfer test and estimand comparison; avoid implying a decision-analysis advance.", "Done in the final Introduction paragraph ('an estimand comparison and transfer test at the scale of continents, not a decision analysis') and in Table 1."),
     ("Pre-trend checks for the DiD; back-cast ISA/tree cover and modelled roughness add error.", "Dated-conversion designs with independent CCI dating and two pre-periods (Fig. 2b); back-cast validated against CCI and LCMAP; roughness removed."),
     ("Foreground the negative DiD; pooled vs city-specific inference; independent mediation validation.", "Fig. 2 and its own Results section foreground the checks; city-level estimates with CIs are in Fig. 1b and Supplementary Table 1 and pooled estimates are labelled as averages; mediation via independent tree cover is shown in Fig. 1c."),
     ("Simulations mirror DML assumptions; present them as assumption checks; add negative-control outcomes and sensitivity bounds.", "Done (Fig. 5 legend, Results section title, Fig. 2c,d)."),
     ("Define interventions; avoid 'wrong' without ground truth; caution on ranking.", "Table 1 defines the interventions; 'wrong' has been removed from the text and title; ranking claims are given with intervals and the zone-baseline comparison."),
     ("Growth: denominator, uncertainty propagation, illustrative only.", "The growth analysis has been removed; the new CMIP6 analysis propagates GCM spread and city-bootstrap uncertainty and is labelled as screening."),
     ("Condition propositions on local verification; separate prediction, causal estimand and decision layers; temper SDG.", "Discussion and Fig. 6c; SDG linkage removed."),
     ("Methods: justify functional form, transfer uncertainty, representativeness, reproducibility.", "Methods justify the linear effect function and its transport limits; bootstrap intervals for transfer; Supplementary Note 1 on representativeness; code and source data provided."),
     ("Show city-level CIs, label benchmarks, add uncertainty and caveats in Fig. 5.", "Fig. 1b shows city-level CIs; benchmarks are labelled in Fig. 4 and Table 2; the former workflow figure is now Fig. 6c, with caveats printed in the panel, and projections carry uncertainty."),
    ])
    D.h('Tracked-change comments in the manuscript', 2)
    R(D, [
     ("0.51 °C is the minimal model and 0.43 °C the own effect; fix the abstract wording.", "The abstract now names the pooled effect and each model's answer separately."),
     ("Narrow 'at scale' to 'across continents'; cite Lee et al. (global urban heat, climate and morphology) and the DML study of 527 Chinese urban clusters.", "Changed to 'at the scale of continents'; both studies are cited in the Introduction (Lee et al. 2026, *Nat. Commun.*; Liu et al. 2026, *Ecol. Indic.*)."),
     ("Replace the overused 'Here we'.", "Removed throughout."),
     ("Define 'c.' or use 'around'/'circa'.", "Epochs are now given as year ranges, so 'c.' no longer appears."),
     ("Move the simulation section after the transfer results.", "Done."),
     ("What does 'richest' imply?", "Replaced by 'with the richest set of predictors', defined as the full conditioning set (NDVI, albedo and tree cover in addition to impervious cover, terrain and climate)."),
     ("A confounder correlation of 0.8 means 'strong'.", "Simulations now use 0.3 (weak), 0.5 (moderate) and 0.8 (strong), labelled as such."),
     ("The prediction interval goes to 1.2; remove 'outside deserts'.", "The Conclusions give zone-specific values and no longer use 'outside deserts'; the prediction interval is reported for a new city-region."),
    ])
    D.save(f'{OUT}/Response_to_Reviewers_126_cities.docx')


if __name__ == '__main__':
    build(); print('ok')
