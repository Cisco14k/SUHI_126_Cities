"""Round-4 response (Nature Sustainability)."""
import sys
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from docxbuild import Doc
from build_ms import S, m, rng, B, pct, OUT, IV, CH, SIM, PR
from build_ms2 import R3, DEC
R4 = S['r4']; XT = R4['ext']['conc']; tot = S['total_wc']['All']; lo_ = S['sens_adj_pool']['mu']
TITLE = 'Predictive accuracy does not reveal the daytime surface heat cost of sealing urban land'
D = Doc(line_numbers=False, spacing=1.15, size=10)
D.para('**Response to the reviewer (round 4)**', size=14, after=6)
D.para(f'Manuscript: “{TITLE}”. Target journal: *Nature Sustainability* (Article).', after=8)
D.para("We thank the reviewer again. In this round we added three analyses (neighbourhood spillover with finer location control, screening against an independent benchmark from dated conversions, and results for European city-regions), narrowed the title and claims, shortened the abstract to three key results, condensed the projection section and Table 1, and closed with a concrete recommendation for sealing policy.", after=10)
items = [
 ("Significance: still a methodological caution; screening gain modest; EU policy hook but only 18 European cities; near-null projection. What changes for planners?",
  f"The Discussion now states three policy consequences and one recommendation: screening for limits on sealing should use total-effect estimators, transferred with their modifiers and uncertainty, and be confirmed locally. We report the 18 European city-regions separately: their effect is larger ({m(R4['eu_total']['mu'])} °C; {m(R4['eu_lag']['mu'])} °C after the lagged-outcome adjustment) and neighbourhood sealing adds {m(R4['eu_sp_nb']['mu'])} °C, so the heat cost of land take is substantial where sealing limits are being introduced. The policy framing now also names growth boundaries, greening quotas and de-sealing targets elsewhere. The projection is reduced to one paragraph stating the finding (warming alone barely changes the heat cost; vegetation does) and its limits."),
 ("Abstract: too many figures; 'ranked cities best' barely holds (63% vs 62%).",
  f"The abstract now gives three results: the plausible range ({m(lo_)}–{m(hi_ := tot['mu'])} °C), that predictive models' implied effects departed from the cities' own estimates by more than the effect, and that a causal transfer model ranked cities better, also against an independent benchmark. The ranking claim is supported where it holds: by Spearman correlation with the own effects ({m(DEC['causal_all']['rho'])} against {m(DEC['full_joint_all']['rho'])} for the mediator-shifted full model) and against dated conversions ({m(XT['causal_all']['rho'][0])} against {m(XT['full_joint_all']['rho'][0])})."),
 ("Introduction: misuse examples are single-city papers; title generalizes beyond what was tested.",
  "Examples now range from single-city studies to multi-city and global syntheses (Logan et al. 2020; Lee et al. 2026; Liu et al. 2026). The title is narrowed to 'daytime surface heat', and the Introduction states that the claims concern daytime surface temperature and gradient-boosted predictive models."),
 ("Study area: rural-dominated; report European cities separately or name non-EU policies.",
  f"Both done (Results, Supplementary Table 11). European cores: {m(R4['eu_core']['mu'])} °C ({R4['eu_core']['k']} cities); fringes {m(R4['eu_fringe']['mu'])} °C."),
 ("Methods: shared spectra in back-cast designs.",
  "Stated as a limitation of the back-cast designs; the confirmation now rests on the concordant design, which requires agreement with the independent ESA CCI product."),
 ("Methods: neighbourhood effect may reflect neighbourhood-scale confounding finer than 5-km bins.",
  f"We re-estimated the joint model with 2-km location bins (Fig. 2c). Own and neighbourhood effects were {m(R4['sp2_own']['mu'])} and {m(R4['sp2_nb']['mu'])} °C, against {m(R3['sp_own']['mu'])} and {m(R3['sp_nb']['mu'])} °C with 5-km bins, so confounding at the 2–5 km scale does not explain the spillover."),
 ("Methods: simulation-derived inflation factor should not be presented as a general calibration.",
  "It is now described as specific to the simulation design and used only as a sensitivity analysis (Methods)."),
 ("Methods: screening is scored against the benchmark that rests on the causal model's assumptions.",
  f"We added an independent benchmark: warming observed at conversions dated by both land-cover products, net of pre-trends, in {XT['n']} city-regions. The ordering of models is unchanged: causal transfer ρ = {m(XT['causal_all']['rho'][0])} (95% CI {rng(XT['causal_all']['rho'][1], XT['causal_all']['rho'][2])}), full GBM {m(XT['full_all']['rho'][0])}, zone baseline {m(XT['zone_baseline']['rho'][0])}, minimal GBM {m(XT['minimal_all']['rho'][0])} (Table 1, Supplementary Table 15). The cities' own estimates correlate with this benchmark at {m(XT['cs3_theta']['rho'][0])}, which also supports them. A CCI-only benchmark is reported but too noisy to discriminate."),
 ("Results: pre-conversion warming 0.08 °C, negative post-period, untestable later cohort; projection adds little.",
  "All three are stated in Results, with the post-period cooling discussed as consistent with partial vegetation recovery or dating error; the projection section is condensed to one paragraph."),
 ("Discussion: 'would misjudge that cost by more than its size' should be conditional.",
  "The consequences are now introduced as 'each conditional on the identification assumptions', and the comparison is stated against the cities' own estimates."),
 ("Limitations: circular benchmark; transferability to European cities.",
  "Both added (fourth and fifth limitations); the independent benchmark is described as noisier and available for 73 city-regions, and 18 European city-regions as too few to characterize the continent."),
 ("Conclusions: close on a concrete recommendation.",
  "The Conclusions end: 'Screening for limits on sealing should therefore use total-effect estimators rather than the perturbations of predictive models, and confirm the screened effects locally.'"),
 ("Grammar and presentation: long, number-heavy sentences; dense Table 1.",
  "The 'checks' section is split into four short paragraphs with fewer numbers; Table 1 now has five columns (prediction skill, difference from own effect, right third, ranking against dated conversions), with the full table in Supplementary Table 15."),
]
for c, r in items:
    D.para(f'**Comment.** *{c}*', after=3, spacing=1.15); D.para(f'**Response.** {r}', after=10, spacing=1.15)
D.save(f'{OUT}/Response_to_Reviewer_round4_126_cities.docx'); print('ok')
