"""Part II - Push x Pull interaction (paper Sections 5.3, 5.5, Appendix C).

Outputs
  tables/interaction_six_specs.csv          paper Table 7 (6 specifications)
  tables/marginal_effects.csv     marginal effects; several SD definitions
  tables/robustness_checks.csv           Table 11 + Appendix C (winsor, two-part, clustering, LOCO ...)
  tables/ppml_iv.csv                     PPML and IV (disclosed, not used for inference)
  tables/quadrants.csv                   observer quadrant means (Section 2.3)
  tables/loo_full_sample.csv             leave-one-country-out, Spec (A) 99.5th and 99th
  tables/sample_integrity_russia.csv         published sample vs Russia 2022-23 restored
  figures/fig_marginal_effects_threshold        marginal effect of sanctions and Infra* threshold
  figures/fig_loo_interaction         leave-one-country-out distribution of alpha_3
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import (AQUA, BLUE, CONTROLS, CS, FE, INK, INK2, MUTED, ORANGE,
                     RED, SANC, Opts, banner, coef, fit_twfe, interaction,
                     load_panel, record, restore_russia, save_fig, save_table,
                     setup_style)


def table7(df):
    rows = []
    for dv, dl in [("rmb_invoicing_w", "Winsorized"), ("rmb_inv_asinh", "Arcsinh")]:
        for lab, infra, x, extra in [("(A) Composite (0-2)", "rmb_infra_it", "infra_x_sanction", ""),
                                     ("(B) CIPS (0/1)", "CIPSit", "cips_x_sanction", " + trend_direct"),
                                     ("(C) Clearing bank (0/1)", "clearing_bank_it", "clear_x_sanction", "")]:
            m = fit_twfe(df, f"{dv} ~ {infra} + {SANC} + {x}{extra} + {CS}{FE}")
            rows.append({"spec": lab, "dv": dl,
                         "a1": m.params[infra], "a1_se": m.std_errors[infra],
                         "a2": m.params[SANC], "a2_se": m.std_errors[SANC], "a2_p": m.pvalues[SANC],
                         "a3": m.params[x], "a3_se": m.std_errors[x], "a3_p": m.pvalues[x],
                         "n": int(m.nobs)})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "interaction_six_specs")
    a = t.iloc[0]
    record("t7_a2", a.a2); record("t7_a2_p", a.a2_p)
    record("t7_a3", a.a3); record("t7_a3_p", a.a3_p); record("t7_n", a.n)
    record("t7_asinh_a3", t.iloc[3].a3)
    record("t7_cips_a3", t.iloc[1].a3); record("t7_clear_a3", t.iloc[2].a3)
    return t


def marginal_effects(df, plt):
    m = interaction(df)
    a2, a3 = m.params[SANC], m.params["infra_x_sanction"]
    V = m.cov
    v22, v33, v23 = V.loc[SANC, SANC], V.loc["infra_x_sanction", "infra_x_sanction"], \
        V.loc[SANC, "infra_x_sanction"]
    thr = -a2 / a3
    g = np.array([-1 / a3, a2 / a3 ** 2])                       # delta method for -a2/a3
    thr_se = float(np.sqrt(g @ np.array([[v22, v23], [v23, v33]]) @ g))
    record("infra_star", thr); record("infra_star_se", thr_se)

    est = df.dropna(subset=["rmb_invoicing_w", "rmb_infra_it", SANC] + CONTROLS)
    sds = {"Sanctioned obs, full panel (closest to paper's 0.11)": df.loc[df[SANC] > 0, SANC].std(),
           "Sanctioned obs, estimation sample": est.loc[est[SANC] > 0, SANC].std(),
           "Estimation sample": est[SANC].std(),
           "Full panel": df[SANC].std()}
    rows = []
    for lab, sd in sds.items():
        rows.append({"sd_definition": lab, "sd": sd,
                     **{f"ME_infra{i}": sd * (a2 + a3 * i) for i in (0, 1, 2)}})
    rows.append({"sd_definition": "Paper Table 8 (Delta = 0.11)", "sd": 0.11,
                 **{f"ME_infra{i}": 0.11 * (a2 + a3 * i) for i in (0, 1, 2)}})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "marginal_effects")
    record("sd_sanc_sanctioned", sds["Sanctioned obs, full panel (closest to paper's 0.11)"])
    record("sd_sanc_estimation", sds["Estimation sample"])

    # ---- figure: ME line + CI (top), distribution of Infra (bottom) - single y-scale each
    x = np.linspace(0, 2, 201)
    me = a2 + a3 * x
    se = np.sqrt(v22 + x ** 2 * v33 + 2 * x * v23)
    lo, hi = me - 1.96 * se, me + 1.96 * se
    fig, (ax, axh) = plt.subplots(2, 1, figsize=(10, 6.6), sharex=True,
                                  gridspec_kw={"height_ratios": [4, 1], "hspace": 0.08})
    ax.fill_between(x, lo, hi, color=BLUE, alpha=0.13, lw=0, label="95% CI (country-clustered)")
    ax.plot(x, me, color=INK, lw=2.5, label="Marginal effect of sanctions")
    ax.axhline(0, color=INK2, lw=0.9)
    ax.axvline(thr, color=ORANGE, ls="--", lw=2)
    ax.annotate(f"Infra* = |α₂|/α₃ ≈ {thr:.2f}", xy=(thr, 0), xytext=(thr + 0.18, a2 * 0.55),
                fontsize=11, fontweight="bold", color=INK,
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5))
    ax.text(0.03, 0.95, "Phase 1: sanctions\nreinforce dollar use", transform=ax.transAxes,
            va="top", fontsize=10, color=INK2)
    ax.text(0.97, 0.95, "Phase 2: sanctions\ndrive RMB adoption", transform=ax.transAxes,
            va="top", ha="right", fontsize=10, color=INK2)
    ax.set_ylabel("∂ RMB invoicing / ∂ Sanctions (pp)")
    ax.set_title("Marginal effect of sanctions on RMB invoicing, by RMB infrastructure")
    ax.legend(loc="lower right")
    vc = est["rmb_infra_it"].round(3).value_counts(normalize=True).sort_index()
    axh.bar(vc.index, vc.values * 100, width=0.06, color=MUTED)
    for k, v in vc.items():
        if v > 0.01:
            axh.text(k, v * 100 + 2, f"{v * 100:.0f}%", ha="center", fontsize=9, color=INK2)
    axh.set_ylim(0, max(vc.values) * 100 * 1.35)
    axh.set_ylabel("% of obs.")
    axh.set_xlabel("RMB infrastructure index (clearing bank + swap line, 0–2)")
    axh.grid(axis="x", visible=False)
    save_fig(fig, "fig_marginal_effects_threshold")
    return m


def robustness(df):
    rows = []

    def add(label, m, var="infra_x_sanction"):
        rows.append({"check": label, **coef(m, var)})

    for q in (0.95, 0.99, 0.995):
        d = df.assign(yq=df.rmb_invoicing_share.clip(upper=df.rmb_invoicing_share.quantile(q)))
        add(f"Winsorize {q * 100:g}th", interaction(d, "yq"))
    add("No winsorization", interaction(df, "rmb_invoicing_share"))
    add("arcsinh DV", interaction(df, "rmb_inv_asinh"))
    add("log(1+y)", interaction(df.assign(l1=np.log1p(df.rmb_invoicing_share)), "l1"))
    anyy = (df.rmb_invoicing_share > 0).astype(float).where(df.rmb_invoicing_share.notna())
    add("Two-part: extensive margin (any RMB invoicing)", interaction(df.assign(anyy=anyy), "anyy"))
    pos = df[df.rmb_invoicing_share > 0].assign(lnpos=lambda d: np.log(d.rmb_invoicing_share))
    add("Two-part: intensive margin (ln y | y>0)", interaction(pos, "lnpos"))
    add("Two-way clustering (country + year)", interaction(df, cluster_time=True))
    add("Drop Russia and China", interaction(df[~df.iso3.isin(["RUS", "CHN"])]))
    add("FE only (no controls)", interaction(df, controls=""))
    for g in (2015, 2016, 2018):
        add(f"Drop {g} CIPS cohort", interaction(df[~(df.g_first_treat == g)]))
    if "CIPS_broad_it" in df.columns:
        m = fit_twfe(df, f"rmb_invoicing_w ~ CIPS_broad_it + {CS}{FE}")
        add("Broad CIPS -> invoicing (main effect)", m, "CIPS_broad_it")
    t = pd.DataFrame(rows)
    save_table(t.round(4), "robustness_checks")
    look = dict(zip(t.check, t.beta))
    record("rob_w95", look["Winsorize 95th"]); record("rob_w99", look["Winsorize 99th"])
    record("rob_w995", look["Winsorize 99.5th"]); record("rob_nowins", look["No winsorization"])
    record("rob_extensive", look["Two-part: extensive margin (any RMB invoicing)"])
    record("rob_log1p", look["log(1+y)"])
    record("rob_dropRUSCHN", look["Drop Russia and China"])
    record("rob_minctrl", look["FE only (no controls)"])
    record("rob_loco2015", look["Drop 2015 CIPS cohort"])
    record("rob_twoway_se", float(t.loc[t.check.str.startswith("Two-way"), "se"].iloc[0]))
    return t


def ppml_iv(df):
    import statsmodels.api as sm
    rows = []
    cols = ["rmb_invoicing_share", "rmb_infra_it", SANC, "infra_x_sanction", "iso3", "year"] + CONTROLS
    d = df[cols].dropna().copy()
    X = pd.concat([d[["rmb_infra_it", SANC, "infra_x_sanction"] + CONTROLS].astype(float),
                   pd.get_dummies(d.iso3, prefix="c", drop_first=True, dtype=float),
                   pd.get_dummies(d.year, prefix="y", drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X)
    m = sm.GLM(d.rmb_invoicing_share.astype(float).values, X.values,
               family=sm.families.Poisson()).fit(maxiter=300)
    for v in ["rmb_infra_it", SANC, "infra_x_sanction"]:
        i = list(X.columns).index(v)
        rows.append({"model": "PPML (A)", "var": v, "beta": m.params[i], "se": m.bse[i], "p": m.pvalues[i]})
    record("ppml_sanc", rows[1]["beta"]); record("ppml_inter", rows[2]["beta"])

    # IV: leave-one-out regional CIPS share (as in the paper; manual 2SLS second stage)
    from .regions import REGION_MAP
    d2 = df.copy()
    d2["region"] = d2.iso3.map(REGION_MAP).fillna("Other")
    tot = d2.groupby(["region", "year"]).CIPSit.agg(["sum", "count"])
    d2 = d2.join(tot, on=["region", "year"])
    d2["regional_cips_share"] = ((d2["sum"] - d2.CIPSit.fillna(0)) / (d2["count"] - 1)).fillna(0)
    iv = d2[["iso3", "year", "clearing_bank_it", "CIPSit", "regional_cips_share",
             "trend_direct"] + CONTROLS].dropna()
    fs = fit_twfe(iv, f"CIPSit ~ regional_cips_share + trend_direct + {CS}{FE}")
    F = float((fs.params["regional_cips_share"] / fs.std_errors["regional_cips_share"]) ** 2)
    rows.append({"model": "IV first stage", "var": "regional_cips_share",
                 "beta": fs.params["regional_cips_share"],
                 "se": fs.std_errors["regional_cips_share"], "p": fs.pvalues["regional_cips_share"],
                 "F": F})
    record("iv_first_stage_F", F)
    save_table(pd.DataFrame(rows).round(4), "ppml_iv")


def quadrants(df):
    obs = df[df.role == "Observer"].groupby("iso3").agg(
        {SANC: "mean", "rmb_infra_it": "mean", "rmb_invoicing_w": "mean"}).dropna()
    obs["s"], obs["i"] = (obs[SANC] > 0).astype(int), (obs.rmb_infra_it > 0).astype(int)
    rows = []
    for s, i, q in [(1, 0, "Q1 sanctioned, no infra"), (1, 1, "Q2 sanctioned + infra"),
                    (0, 0, "Q3 status quo"), (0, 1, "Q4 voluntary adoption")]:
        sub = obs[(obs.s == s) & (obs.i == i)]
        rows.append({"quadrant": q, "n_countries": len(sub), "mean_invoicing": sub.rmb_invoicing_w.mean()})
    t = pd.DataFrame(rows)
    save_table(t.round(3), "quadrants")
    record("quad_Q1", t.iloc[0].mean_invoicing); record("quad_Q2", t.iloc[1].mean_invoicing)


def loo(df, plt):
    out = {}
    for lab, q in [("spec_A_99.5", 0.995), ("w99", 0.99)]:
        d = df.assign(yq=df.rmb_invoicing_share.clip(upper=df.rmb_invoicing_share.quantile(q)))
        full = interaction(d, "yq")
        countries = sorted(d.dropna(subset=["yq", "rmb_infra_it", SANC] + CONTROLS).iso3.unique())
        rows = []
        for c in countries:
            m = interaction(d[d.iso3 != c], "yq")
            rows.append({"dropped": c, **coef(m, "infra_x_sanction")})
        t = pd.DataFrame(rows)
        t["spec"] = lab
        out[lab] = (full, t)
        npos, nsig = int((t.beta > 0).sum()), int((t.p < 0.05).sum())
        print(f"    LOO {lab}: {len(t)} refits | positive {npos} | p<0.05 {nsig} | "
              f"range [{t.beta.min():.3f}, {t.beta.max():.3f}] | "
              f"median |Δ| {np.median(abs(t.beta - full.params['infra_x_sanction'])):.3f}")
        record(f"loo_{lab}_n", len(t)); record(f"loo_{lab}_pos", npos); record(f"loo_{lab}_sig05", nsig)
        r = t[t.dropped == "RUS"].iloc[0]
        record(f"loo_{lab}_noRUS_beta", r.beta); record(f"loo_{lab}_noRUS_p", r.p)
    save_table(pd.concat([v[1] for v in out.values()]).round(4), "loo_full_sample")

    full, t = out["spec_A_99.5"]
    t = t.sort_values("beta").reset_index(drop=True)
    b0 = full.params["infra_x_sanction"]
    fig, ax = plt.subplots(figsize=(10, 4.8))
    xs = np.arange(len(t))
    ax.vlines(xs, t.beta - 1.96 * t.se, t.beta + 1.96 * t.se, color=MUTED, lw=1)
    ax.scatter(xs, t.beta, s=14, color=BLUE, zorder=3, label="α₃ excluding one country")
    for c in ["RUS"]:
        k = t.index[t.dropped == c][0]
        ax.vlines(k, t.beta[k] - 1.96 * t.se[k], t.beta[k] + 1.96 * t.se[k], color=RED, lw=2)
        ax.scatter([k], [t.beta[k]], s=60, color=RED, zorder=4)
        ax.annotate(f"excl. Russia: {t.beta[k]:+.2f} (p = {t.p[k]:.3f})", xy=(k, t.beta[k]),
                    xytext=(-14, 0), textcoords="offset points", fontsize=10, ha="right", va="center", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    ax.axhline(b0, color=INK2, ls="--", lw=1.2, label=f"Full sample α₃ = {b0:+.3f}")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.set_xticks([])
    ax.set_xlabel(f"{len(t)} leave-one-country-out re-estimates, sorted")
    ax.set_ylabel("α₃ (Infra × Sanctions), 95% CI")
    npos, nsig = int((t.beta > 0).sum()), int((t.p < 0.05).sum())
    ax.set_title(f"Leave-one-country-out: α₃ > 0 in {npos}/{len(t)}, p < 0.05 in {nsig}/{len(t)}")
    ax.legend(loc="upper left")
    save_fig(fig, "fig_loo_interaction")


def sample_integrity(df):
    rows = []
    C7 = " + ".join(c for c in CONTROLS if c != "financial_depth_it")
    for lab, d, ctrl in [("Published sample", df, CS),
                         ("Russia 2022-23 restored (LOCF fin. depth)", restore_russia(df), CS),
                         ("Without financial-depth control", df, C7)]:
        m = interaction(d, controls=ctrl)
        a2, a3 = m.params[SANC], m.params["infra_x_sanction"]
        rows.append({"sample": lab, "a2": a2, "a3": a3, "a3_p": m.pvalues["infra_x_sanction"],
                     "infra_star": -a2 / a3, "n": int(m.nobs)})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "sample_integrity_russia")
    record("restored_a3", t.iloc[1].a3); record("restored_infra_star", t.iloc[1].infra_star)
    d = df.dropna(subset=["rmb_invoicing_w", "rmb_infra_it", SANC] + CONTROLS)
    record("post2022_obs_with_invoicing", int(df[(df.year >= 2022) & df.rmb_invoicing_share.notna()].shape[0]))
    record("post2022_obs_in_regression", int(d[d.year >= 2022].shape[0]))
    print(t.round(3).to_string(index=False))


def run():
    banner("S02  PART II - Push x Pull interaction")
    plt = setup_style()
    df = load_panel()
    table7(df)
    marginal_effects(df, plt)
    robustness(df)
    ppml_iv(df)
    quadrants(df)
    sample_integrity(df)
    loo(df, plt)


if __name__ == "__main__":
    run()
