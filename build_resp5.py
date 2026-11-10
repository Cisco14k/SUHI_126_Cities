"""Round-5 response (Nature Sustainability)."""
import sys
sys.path.insert(0, '/home/claude/w126/scripts'); from common import *
from docxbuild import Doc
from build_ms import S, m, rng, B, pct, OUT, IV
from build_ms2 import R3, DEC
R4, R5 = S['r4'], S['r5']; XT = R4['ext']['conc']; XC = R5['ext_ccidose']; tot = S['total_wc']['All']; lo_ = S['sens_adj_pool']['mu']
TITLE = 'Predictive accuracy does not reveal the daytime surface heat cost of sealing urban land'
rr = R5['rho_by_region']; nb = sum(v['causal'] > v['full'] for v in rr.values())
D = Doc(line_numbers=False, spacing=1.15, size=10)
D.para('**Response to the reviewer (round 5)**', size=14, after=6)
D.para(f'Manuscript: “{TITLE}”. Target journal: *Nature Sustainability* (Article).', after=8)
D.para("We thank the reviewer. We added two analyses (the dated-conversion benchmark with ESA CCI change as the dose, and the lagged-outcome design restricted to cells still vegetated in 1985–1989), characterized the benchmark cities, and revised the wording requested.", after=10)
items = [
 ("Abstract: the range mixes a bound with an estimate; 'none in arid cities' overstates; 'more than the effect itself' depends on the own estimates; opening joins two topics.",
  f"The abstract now reads 'an estimated {m(tot['mu'])} °C ({m(lo_)} °C after bias adjustment)', 'no detectable warming in arid cities', and 'departed from the cities' causal estimates by more than the effect itself'. The opening is one framing sentence linking sealing limits to how their heat benefits are judged (150 words)."),
 ("Introduction: shorten the policy opening; 'has not been tested' is strong.",
  "The opening paragraph is shortened and the gap now reads 'has not been quantified across climates and continents'."),
 ("Study area: justify circular city-regions; 18 European cities give an indication, not a European estimate.",
  "Methods now justify circles (uniform footprint independent of administrative definitions, inclusion of the rural background and fringe, no boundaries drawn after the conversions studied). The European results are framed as an indication, and the Limitations state that 18 city-regions cannot characterize the continent."),
 ("Methods: the 'independent' benchmark is itself DML-based and uses the back-cast dose.",
  f"We say so explicitly and repeated it with the ESA CCI change as the dose, so that dating and dose are both independent of Landsat. The order of models is unchanged: causal {m(XC['causal_all']['rho'][0])}, full {m(XC['full_all']['rho'][0])}, zone baseline {m(XC['zone_baseline']['rho'][0])}, minimal {m(XC['minimal_all']['rho'][0])} (Supplementary Table 17). The CCI-dosed conversion effect is {m(R5['cc_post']['mu'])} °C during against {m(R5['cc_pre1']['mu'])} °C before conversion (net {m(R5['cc_net']['mu'])} °C, 95% CI {rng(R5['cc_net']['lo'], R5['cc_net']['hi'])}), per ten percentage points of CCI urban fraction."),
 ("Methods: the 73 benchmark cities may not be representative.",
  f"Their own effects resemble those of the other cities ({m(R5['sel_pool_in']['mu'])} against {m(R5['sel_pool_out']['mu'])} °C; Mann–Whitney P = {m(R5['sel_p'])}), but arid and continental cities are over-represented; both facts are reported in Results and Limitations (Supplementary Table 16)."),
 ("Methods: the lagged-outcome design may over-control if land was cleared before sealing.",
  f"We agree and tested it. In cells still vegetated in 1985–1989, where clearing had not occurred, the adjustment changed the effect only from {m(R5['lagveg_ref']['mu'])} to {m(R5['lagveg']['mu'])} °C, much less than in all unsealed cells. The lagged estimates are now described as lower bounds rather than corrections."),
 ("Results: non-zero pre-trend, untestable later cohort, Europe ranking reversal, wide city-level intervals; ranking advantage holds on average, not everywhere.",
  f"All are stated. A new paragraph begins 'The ranking advantage holds on average, not everywhere': the causal model ranks cities better than the full model in {nb} of seven world regions and worse in the others, including Europe."),
 ("Discussion: label the warming statement as space-for-time with vegetation fixed; 'absent' should be 'not detected'.",
  "Done in Results and Discussion."),
 ("Limitations: selection of benchmark cities; possible over-adjustment.",
  "Both added; the list now has eight limitations."),
 ("Conclusions: same caution on the range and on Europe.",
  "The Conclusions use the same wording as the abstract ('an estimated … ( … after bias adjustment)', 'no detectable warming in arid cities')."),
 ("Grammar: long sentences in the screening paragraph; abstract opening.",
  "The screening paragraph is split into two, with the European comparison in a separate paragraph; the abstract opening is a single framing sentence."),
]
for c, r in items:
    D.para(f'**Comment.** *{c}*', after=3, spacing=1.15); D.para(f'**Response.** {r}', after=10, spacing=1.15)
D.save(f'{OUT}/Response_to_Reviewer_round5_126_cities.docx'); print('ok')
