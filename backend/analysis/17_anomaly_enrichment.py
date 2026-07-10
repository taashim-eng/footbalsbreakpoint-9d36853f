"""
17_anomaly_enrichment.py — PhD-level statistical enrichment of the break-window
anomaly question, computed entirely from REAL observed data.

Scientific question
-------------------
Do lower-GDP ("Group B") teams concede *specifically more* during the
hydration-break window (65'-80') than higher-GDP ("Group A") teams — beyond
what their overall quality and match context already explain?

Design
------
1. Recompute a clean team-match-window panel directly from the `events` table
   (goals conceded by each side in [0-45), [45-65), [65-80), [80-90+]).
2. Restrict to genuine cross-group matches (exactly one A team vs one B team).
3. Layered inference, weakest-to-strongest control:
     (a) Unpaired rate comparison  -> rate ratio, Wilson CIs, chi-square, Cramér's V
     (b) Paired within-match test   -> McNemar (controls for shared match context)
     (c) Difference-in-differences  -> break-vs-baseline, B-vs-A, bootstrap CI
                                       (controls for each team's own baseline)
     (d) Adjusted Poisson GLM        -> covariate control (WBGT, rank gap, leading)
4. Benjamini-Hochberg FDR control across the confirmatory family.
5. 2026 per-match shock index from a Poisson goals model (score-only data).

Outputs a single results JSON consumed by the report and by the 2026 data
enrichment. Deterministic (fixed bootstrap seed).
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

from backend import config

SEED = config.RANDOM_SEED
rng = np.random.default_rng(SEED)

OUT_DIR = os.path.join(str(config.OUTPUT_DIR), "enrichment")
# Baseline "settle" window is 15 minutes wide (50-65) to exactly match the
# 15-minute break window (65-80), so the difference-in-differences compares
# equal-width exposure windows.
WINDOWS = {"early": (0, 45), "settle": (50, 65), "break": (65, 80), "late": (80, 200)}


# ── Panel construction from real events ──────────────────────────────────────

def build_panel(conn):
    ad = pd.read_sql_query(
        "SELECT * FROM analysis_dataset WHERE tournament_year != 2026", conn)
    ev = pd.read_sql_query(
        "SELECT match_id, minute, event_type, team FROM events "
        "WHERE event_type IN ('goal','penalty','own_goal')", conn)
    ev_by_match = {mid: g for mid, g in ev.groupby("match_id")}

    rows = []
    for _, r in ad.iterrows():
        if r["gdp_group_home"] == r["gdp_group_away"]:
            continue  # not a genuine A-vs-B match
        g = ev_by_match.get(r["match_id"])
        home_min, away_min = [], []
        if g is not None:
            for _, e in g.iterrows():
                m = int(e["minute"])
                scorer_is_home = e["team"] == r["team_home"]
                if e["event_type"] == "own_goal":
                    scorer_is_home = not scorer_is_home  # own goal credits opponent
                (home_min if scorer_is_home else away_min).append(m)

        def conceded(side_scored_min, lo, hi):
            return sum(1 for m in side_scored_min if lo <= m < hi)

        # home concedes what away scored, and vice versa
        for side, grp, opp_min, own_score_65, opp_score_65, rank, opp_rank in [
            ("home", r["gdp_group_home"], away_min,
             sum(1 for m in home_min if m < 65), sum(1 for m in away_min if m < 65),
             r["fifa_rank_home"], r["fifa_rank_away"]),
            ("away", r["gdp_group_away"], home_min,
             sum(1 for m in away_min if m < 65), sum(1 for m in home_min if m < 65),
             r["fifa_rank_away"], r["fifa_rank_home"]),
        ]:
            rows.append({
                "match_id": r["match_id"], "era": r["era"],
                "year": int(r["tournament_year"]), "side": side,
                "group": grp,
                "conc_break": conceded(opp_min, *WINDOWS["break"]),
                "conc_settle": conceded(opp_min, *WINDOWS["settle"]),
                "conc_early": conceded(opp_min, *WINDOWS["early"]),
                "conc_late": conceded(opp_min, *WINDOWS["late"]),
                "leading_65": int(own_score_65 > opp_score_65),
                "wbgt": r["wbgt_estimate"], "rank": rank,
                "rank_gap": rank - opp_rank,  # positive = weaker (higher rank number)
            })
    return pd.DataFrame(rows)


# ── Helpers ──────────────────────────────────────────────────────────────────

def wilson_ci(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0, center - half), min(1, center + half))


def cramers_v(table):
    chi2 = stats.chi2_contingency(table, correction=False)[0]
    n = table.sum()
    return np.sqrt(chi2 / (n * (min(table.shape) - 1)))


# ── Analyses ─────────────────────────────────────────────────────────────────

def analyze(panel):
    B = panel[panel.group == "B"]
    A = panel[panel.group == "A"]
    res = {}

    # (a) Unpaired break-window concession comparison
    kB, nB = int((B.conc_break > 0).sum()), len(B)
    kA, nA = int((A.conc_break > 0).sum()), len(A)
    pB, pA = kB / nB, kA / nA
    table = np.array([[kB, nB - kB], [kA, nA - kA]])
    chi2, p_chi, _, _ = stats.chi2_contingency(table, correction=False)
    res["unpaired"] = {
        "n_B": nB, "n_A": nA,
        "break_concede_rate_B": round(pB, 4), "break_concede_rate_A": round(pA, 4),
        "ci_B": [round(x, 4) for x in wilson_ci(kB, nB)],
        "ci_A": [round(x, 4) for x in wilson_ci(kA, nA)],
        "rate_ratio": round(pB / pA, 3) if pA > 0 else None,
        "risk_difference_pct": round((pB - pA) * 100, 2),
        "chi2": round(chi2, 3), "p_value": float(f"{p_chi:.2e}"),
        "cramers_v": round(cramers_v(table), 4),
        "mean_conc_break_B": round(B.conc_break.mean(), 4),
        "mean_conc_break_A": round(A.conc_break.mean(), 4),
    }

    # (b) Paired within-match McNemar (B vs A conceded in break window, same match)
    wide = panel.pivot_table(index="match_id", columns="group",
                             values="conc_break", aggfunc="max").dropna()
    b_yes = (wide["B"] > 0)
    a_yes = (wide["A"] > 0)
    n10 = int((b_yes & ~a_yes).sum())   # only B conceded
    n01 = int((~b_yes & a_yes).sum())   # only A conceded
    mcnemar_stat = (abs(n10 - n01) - 1) ** 2 / (n10 + n01) if (n10 + n01) > 0 else 0.0
    p_mcnemar = 1 - stats.chi2.cdf(mcnemar_stat, df=1)
    res["paired_mcnemar"] = {
        "n_matches": int(len(wide)),
        "only_B_conceded": n10, "only_A_conceded": n01,
        "discordant_ratio": round(n10 / n01, 3) if n01 > 0 else None,
        "statistic": round(mcnemar_stat, 3), "p_value": round(float(p_mcnemar), 4),
    }

    # (c) Difference-in-differences: (break - settle baseline), B vs A.
    # Per-match "within-difference" d_i = (B break-baseline) - (A break-baseline);
    # the DiD is mean(d_i), and a cluster (match-level) bootstrap on d_i gives the CI.
    mm = panel.pivot_table(index="match_id", columns="group",
                           values=["conc_break", "conc_settle"], aggfunc="max").dropna()
    d = ((mm[("conc_break", "B")] - mm[("conc_settle", "B")])
         - (mm[("conc_break", "A")] - mm[("conc_settle", "A")])).to_numpy()
    did = d.mean()
    boot = d[rng.integers(0, len(d), size=(5000, len(d)))].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    res["did_break_vs_baseline"] = {
        "estimate": round(float(did), 4),
        "ci": [round(float(lo), 4), round(float(hi), 4)],
        "interpretation": "extra break-window concessions by B beyond A, net of each side's own 50-65 (equal-width) baseline",
        "crosses_zero": bool(lo <= 0 <= hi),
    }

    # (d) Adjusted Poisson GLM
    panel = panel.copy()
    panel["is_B"] = (panel.group == "B").astype(int)
    panel["wbgt_c"] = panel["wbgt"] - panel["wbgt"].mean()
    panel["rank_gap_c"] = (panel["rank_gap"] - panel["rank_gap"].mean()) / panel["rank_gap"].std()
    model = smf.glm(
        "conc_break ~ is_B + wbgt_c + rank_gap_c + leading_65 + C(era)",
        data=panel, family=sm.families.Poisson()).fit(cov_type="cluster",
                                                       cov_kwds={"groups": panel["match_id"]})
    irr = np.exp(model.params["is_B"])
    ci_lo, ci_hi = np.exp(model.conf_int().loc["is_B"])
    res["adjusted_poisson"] = {
        "gdp_irr": round(float(irr), 3),
        "gdp_irr_ci": [round(float(ci_lo), 3), round(float(ci_hi), 3)],
        "gdp_p_value": round(float(model.pvalues["is_B"]), 4),
        "wbgt_irr_per_degree": round(float(np.exp(model.params["wbgt_c"])), 3),
        "wbgt_p": round(float(model.pvalues["wbgt_c"]), 4),
        "rank_gap_irr": round(float(np.exp(model.params["rank_gap_c"])), 3),
        "rank_gap_p": round(float(model.pvalues["rank_gap_c"]), 4),
        "note": "IRR = incidence-rate ratio; >1 means more break-window concessions. Clustered SE by match.",
    }

    # BH-FDR across the confirmatory family
    fam = {
        "unpaired_chi2": res["unpaired"]["p_value"],
        "paired_mcnemar": res["paired_mcnemar"]["p_value"],
        "adjusted_gdp": res["adjusted_poisson"]["gdp_p_value"],
    }
    names = list(fam)
    pvals = np.array([fam[n] for n in names])
    order = np.argsort(pvals)
    m = len(pvals)
    bh = np.empty(m)
    prev = 1.0
    for rank_i, idx in enumerate(reversed(order)):
        i = m - rank_i
        val = min(prev, pvals[idx] * m / i)
        bh[idx] = val
        prev = val
    res["fdr_bh"] = {names[i]: round(float(bh[i]), 4) for i in range(m)}

    # Per-era trend of the break-window B-A gap
    trend = []
    for era in ["A", "B", "C"]:
        pe = panel[panel.era == era]
        b = pe[pe.group == "B"].conc_break
        a = pe[pe.group == "A"].conc_break
        gap = b.mean() - a.mean()
        # 95% CI via normal approx on difference of means
        se = np.sqrt(b.var(ddof=1) / len(b) + a.var(ddof=1) / len(a))
        trend.append({
            "era": era, "n_matches": int(len(pe) / 2),
            "mean_conc_break_B": round(float(b.mean()), 4),
            "mean_conc_break_A": round(float(a.mean()), 4),
            "gap": round(float(gap), 4),
            "gap_ci": [round(float(gap - 1.96 * se), 4), round(float(gap + 1.96 * se), 4)],
        })
    res["era_trend"] = trend
    return res


# ── 2026 per-match shock index (Poisson surprisal) ───────────────────────────

def shock_index_2026(artifact_path):
    with open(artifact_path, encoding="utf-8") as f:
        data = json.load(f)
    matches = data["matches"]

    # Estimate each team's attack (goals-for rate) and defense (goals-against
    # rate) from all their observed 2026 matches, plus league baseline.
    gf, ga, gp = {}, {}, {}
    total_goals = 0
    for m in matches:
        h, a = m["homeTeam"], m["awayTeam"]
        sh, sa = m["finalScore"]["home"], m["finalScore"]["away"]
        for t in (h, a):
            gf.setdefault(t, 0); ga.setdefault(t, 0); gp.setdefault(t, 0)
        gf[h] += sh; ga[h] += sa; gp[h] += 1
        gf[a] += sa; ga[a] += sh; gp[a] += 1
        total_goals += sh + sa
    league_avg = total_goals / (2 * len(matches))  # goals per team per match

    # Shrink team rates toward the league mean (small samples -> regress to mean).
    K = 3.0  # pseudo-matches of prior weight
    def attack(t): return (gf[t] + K * league_avg) / (gp[t] + K)
    def defense(t): return (ga[t] + K * league_avg) / (gp[t] + K)

    enriched = []
    for m in matches:
        h, a = m["homeTeam"], m["awayTeam"]
        sh, sa = m["finalScore"]["home"], m["finalScore"]["away"]
        # expected goals: blend team attack with opponent defense
        lam_h = max(0.15, (attack(h) + defense(a)) / 2)
        lam_a = max(0.15, (attack(a) + defense(h)) / 2)
        p_score = stats.poisson.pmf(sh, lam_h) * stats.poisson.pmf(sa, lam_a)
        surprisal = float(-np.log(max(p_score, 1e-9)))
        # win-probability of the actual winner pre-match (Poisson-Poisson)
        pw_h, pw_a, pw_d = _match_probs(lam_h, lam_a)
        if sh > sa:
            winner_prob = pw_h
        elif sa > sh:
            winner_prob = pw_a
        else:
            winner_prob = pw_d
        enriched.append({
            "matchId": m["matchId"],
            "expectedGoals": {"home": round(lam_h, 2), "away": round(lam_a, 2)},
            "shockIndex": round(surprisal, 2),
            "resultProbability": round(float(p_score), 4),
            "winnerPreMatchProb": round(float(winner_prob), 3),
        })
    # percentile rank of shock (0-100) for readability
    shocks = np.array([e["shockIndex"] for e in enriched])
    for e in enriched:
        e["shockPercentile"] = int(round(100 * (shocks < e["shockIndex"]).mean()))
    return {"league_goals_per_team": round(league_avg, 3), "matches": enriched}


def _match_probs(lam_h, lam_a, max_goals=10):
    ph = stats.poisson.pmf(np.arange(max_goals + 1), lam_h)
    pa = stats.poisson.pmf(np.arange(max_goals + 1), lam_a)
    joint = np.outer(ph, pa)
    home = np.tril(joint, -1).sum()
    away = np.triu(joint, 1).sum()
    draw = np.trace(joint)
    return float(home), float(away), float(draw)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    panel = build_panel(conn)
    conn.close()
    print(f"Panel: {len(panel)} team-match rows "
          f"({panel.match_id.nunique()} cross-group matches).")
    results = {
        "meta": {
            "sample": "genuine cross-group (one Group-A vs one Group-B team) historical "
                      "matches, 2002-2022 World Cups + 2003-2019 continental cups",
            "n_cross_group_matches": int(panel.match_id.nunique()),
            "seed": SEED,
            "data_source": "worldcup.db events table (real observed goals)",
        },
        "historical": analyze(panel),
    }
    art = os.path.join(str(config.RAW_DIR), "wc2026_results.json")
    if os.path.exists(art):
        results["shock2026"] = shock_index_2026(art)
    with open(os.path.join(OUT_DIR, "enrichment_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Saved enrichment_results.json")
    return results


def run_anomaly_enrichment():
    """Pipeline entry point (matches the naming convention of the other modules)."""
    return main()


if __name__ == "__main__":
    import pprint
    r = main()
    pprint.pprint(r["historical"]["unpaired"])
    pprint.pprint(r["historical"]["did_break_vs_baseline"])
    pprint.pprint(r["historical"]["adjusted_poisson"])
