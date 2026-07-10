# Adversarial E2E review — five PhD personas

Round run 2026-07-09 against the full pipeline, the enrichment analysis
(`17_anomaly_enrichment.py`), the exported data, and the report. Findings are
severity-ranked (P0 blocker → P3 nit). Every claim below is recomputed from real
data; external context is cited in `EXTERNAL_FACTS.md`.

**Headline outcome:** the review *changed the conclusion*. The previous "flat
debunk — it's all confounding" was itself overstated. The corrected finding is
more nuanced (and more interesting): the pooled anomaly is confounded and
underpowered, **but** a heat-conditioned, strength-adjusted GDP effect survives
as an exploratory lead pointing to socioeconomic heat vulnerability — not
manipulation — and our goal-based data is structurally blind to the spot-fixing
and refereeing where documented integrity risk actually lives.

---

## PhD Data Scientist

| # | Sev | Finding | Resolution |
|---|-----|---------|------------|
| DS1 | **P1** | "Explained away" overclaims a null. The study is **underpowered**: minimum detectable rate ratio at 80% power is **1.55**, above the observed **1.29**. TOST cannot reject a +50% effect (p=0.24); it can only reject a doubling (IRR 2.0, p=0.011). | Added power + TOST equivalence block. Report reframed to "no evidence of an effect, not proof of none." |
| DS2 | **P1** | No subgroup exploration. Cooling breaks are heat-triggered, yet heat was only a covariate. | Added GDP×heat interaction (**IRR 1.13/°C, p=0.024**) and a hot-tercile model: **rank-adjusted GDP IRR 2.21 [1.18–4.15], p=0.014** — survives strength adjustment. Conclusion rewritten. |
| DS3 | P3 | FDR family excluded the era subgroup tests. | Era A/B/C chi-square p-values folded into Benjamini-Hochberg (min q now **0.245**; era C's uncorrected p=0.046 does not survive). |

## PhD Actuarial Scientist

| # | Sev | Finding | Resolution |
|---|-----|---------|------------|
| AC1 | **P2** | Shock model used independent Poisson — it mis-prices correlated low scores and under-weights draws, biasing `winnerPreMatchProb`. | Added a **Dixon-Coles** low-score correction (τ, ρ=−0.10) to the joint score grid; used for both surprisal and match-result probabilities. |
| AC2 | P3 | Credibility shrinkage (K=3 pseudo-matches) and ρ are fixed, not fitted. | Documented as deliberate priors for a 3-match-sample tournament; ρ conventional (can't be fit cleanly at this n). Exposed `dixon_coles_rho` / `shrinkage_pseudomatches` in the output. |
| AC3 | P3 | "expectedGoals" risks implying shot-based xG. | Clarified in report + ELI5: it is a **rate-based** model expectation (goals-for/against rates), not shot xG. |

## PhD Mathematician

| # | Sev | Finding | Resolution |
|---|-----|---------|------------|
| MA1 | — | Verified correct: Wilson score CIs, McNemar with continuity correction, Greenwood survival CIs, log-ratio forest axis, and the cluster (match-level) bootstrap on per-match differences. | No change needed. |
| MA2 | **P2** | Garden-of-forking-paths risk: interaction/subgroup tests must not be sold as confirmatory. | Split reporting into a **pre-specified confirmatory family** (FDR-controlled) and clearly-labelled **exploratory** heat analyses. Report states this explicitly. |
| MA3 | P3 | BH implementation should enforce monotonicity. | Confirmed the step-up monotone enforcement is correct; added `fdr_bh_min_q`. |

## PhD Sociologist

| # | Sev | Finding | Resolution |
|---|-----|---------|------------|
| SO1 | **P2** | GDP median-split is a crude, dichotomised proxy that conflates *economic development* with *football infrastructure/history* (Brazil/Argentina are football-rich but not top-GDP; strong African sides sit in "Group B"). Weak construct validity; dichotomisation discards information. | Report foregrounds FIFA **ranking** (football-specific strength, used continuously in models) as the better-behaved variable, and interprets the surviving heat×GDP effect as **socioeconomic heat vulnerability** (preparation, acclimatisation, sports-science budgets), not manipulation. |
| SO2 | P3 | "Anomaly detection / following the money" framing primes a conspiracy reading. | Report separates **motive from evidence** and retains/strengthens "anomaly ≠ wrongdoing." |

## PhD Sports Scientist

| # | Sev | Finding | Resolution |
|---|-----|---------|------------|
| SP1 | **P1** | The 65′–80′ "break window" is a fixed proxy; it does **not** verify the actual cooling break, which is heat-triggered (WBGT ≈ 32 °C) and taken ~30′ and ~75′ — and only in hot matches. Historical break-occurrence isn't in the data. So a "break effect" cannot be cleanly identified. | Stated as a key limitation; motivated the heat-conditioned analysis; noted our ~27 °C tercile threshold is **milder** than the real ~32 °C trigger, so the hot-subgroup effect is a floor, not a clean break test. |
| SP2 | **P2** | Late-game concessions are a general phenomenon (fatigue, chasing the game, bench depth). Richer federations' deeper squads/fitness explain better late-game defence — a benign mechanism behind the rank effect and the heat×GDP effect. | Added mechanism discussion; the surviving hot-match GDP effect is framed as resource/acclimatisation inequality. |
| SP3 | **P2** | Within hot matches, the difference-in-differences spans zero (**+0.03, CI [−0.17,+0.21]**) — the hot effect is **not shown to be break-specific**. | Conclusion states "general heat vulnerability," not "cooling-break collapse." |

## Cross-cutting: external overlay (corruption / gambling / revenue)

Per `EXTERNAL_FACTS.md` — all documented, none joined to match records:
- **Documented FIFA corruption is administrative** (media/marketing-rights bribery; 2015 US DOJ case, ~$150m; Blatter & Platini acquitted of criminal fraud) — not on-pitch WC result-fixing.
- **Proven match-fixing** sits in qualifiers / lower tiers / referees (Nepal, Chaibou, Siasia, Lu Jun) — not the WC-finals matches in our 2002–2022 sample.
- **Modern 2026 risk is spot-fixing** (cards/corners; the Wahi referral) and **refereeing** (Egypt's complaint re: Argentina's Round of 16) — both **invisible to a goals/scoreline analysis**. This is a scope limitation, not evidence of anything.
- **Motive is real and large** ($7.6 bn → projected $11–13 bn FIFA revenue; UNODC-estimated $1.7 tn illegal betting market) — but motive ≠ evidence.

**Verdict:** our result-based analysis is silent on precisely the vectors where
documented integrity failures and the strongest incentives live. Say so plainly;
infer nothing.
