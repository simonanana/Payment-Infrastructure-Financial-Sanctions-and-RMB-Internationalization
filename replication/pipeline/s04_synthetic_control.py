"""Part III - (penalized) synthetic control for Russia 2022 (paper Section 7).

Reproduces 09_scm_penalized_v2(.ipynb) and its _finalize notebook with the same
SLSQP set-up, then adds donor-informativeness and data-provenance diagnostics.

Needs the full panel (MASTER_PANEL_v25b_clean.csv) for the BMP outcome; with
only the repository panel the BMP parts are skipped and reported as such.

Outputs
  tables/structural_ranking.csv      5-covariate distance to Russia (all 154 countries)
  tables/brics_hypergeometric.csv         over-representation test under three definitions
  tables/scm_lambda_sweep.csv            gap / pre-RMSE / top donors by lambda (Table J2)
  tables/scm_lambda_cv.csv               leave-one-pre-year-out CV error by lambda
  tables/scm_placebo_inference.csv          placebo p-values: paper vs informative donors
  tables/scm_donor_informativeness.csv  constant-pre-period donors by outcome
  tables/settlement_proxy_forensics.csv    proxy vs China-trade x SWIFT product; Russia 2016-23
  figures/fig_scm_lambda_sweep           post gap and pre-RMSE vs lambda (separate panels)
  figures/fig_scm_donor_weights          donor composition by lambda
  figures/fig_scm_bmp_clearing                   (a) BMP, (b) clearing-bank falsification
  figures/fig_scm_three_outcomes   paper Figure 5 with the settlement panel annotated
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import hypergeom

from .common import (AQUA, BLUE, GRID, INK, INK2, MUTED, ORANGE, RED, Opts,
                     banner, record, save_fig, save_table, setup_style)

TREATED, T_YEAR = "RUS", 2022
PRE = list(range(2010, T_YEAR))
EXCLUDE = ["UKR", "BLR", "RUS"]
COVARS = ["ln_gdp", "ln_trade_openness", "capital_openness_it_filled",
          "financial_depth_it", "fdi_inflow_gdp_it_w"]
LAMBDAS = [0.0, 0.01, 0.1, 1.0, 10.0, 100.0]
OUTCOMES = {"bmp_premium_arcsinh": "Black-market FX premium (arcsinh)",
            "rmb_settlement_proxy_it": "SWIFT-observable RMB settlement proxy",
            "clearing_bank_it": "Clearing-bank indicator (falsification)"}

# BRICS status as of 2025 (verify before presenting; dates in README)
BRICS_MEMBERS = {"BRA", "IND", "CHN", "ZAF", "EGY", "ETH", "IRN", "ARE", "IDN"}   # excl. RUS
BRICS_INVITED = {"SAU", "TUR"}                                                    # invited, not confirmed
BRICS_PARTNERS = {"BLR", "BOL", "KAZ", "CUB", "MYS", "THA", "UGA", "UZB", "NGA", "VNM"}


# ----------------------------------------------------------------- SCM core
def get_donors(df, dv, pre=PRE, min_cov=0.8):
    c = df[~df.iso3.isin(EXCLUDE)]
    for f in ("fin_centre_flag", "dollarised_flag"):
        if f in c.columns:
            c = c[c[f] != 1]
    comp = c[c.year.isin(pre)].groupby("iso3")[dv].apply(lambda x: x.notna().sum())
    return comp[comp >= int(np.ceil(len(pre) * min_cov))].index.tolist()


def outcome_matrices(df, dv, treated, donors):
    yrs = sorted(PRE + list(range(T_YEAR, int(df.year.max()) + 1)))
    y = df[(df.iso3 == treated) & df.year.isin(yrs)].set_index("year")[dv].reindex(yrs)
    Y = pd.concat([df[(df.iso3 == d) & df.year.isin(yrs)].set_index("year")[dv]
                   .reindex(yrs).rename(d) for d in donors], axis=1).dropna(axis=1)
    idx = y.dropna().index.intersection(Y.dropna().index)
    return y.loc[idx], Y.loc[idx]


def covariate_vectors(df, treated, donors):
    pre = df[df.year.isin(PRE)]
    t = pre[pre.iso3 == treated][COVARS].mean()
    d = pre[pre.iso3.isin(donors)].groupby("iso3")[COVARS].mean().reindex(donors).dropna()
    pooled = pd.concat([t.to_frame().T, d])
    mu, sd = pooled.mean(), pooled.std(ddof=0).replace(0, 1.0)
    return ((t - mu) / sd).values, ((d - mu) / sd).values.T, list(d.index)


def weights(y, Y, pre, xt=None, Xd=None, lam=0.0):
    m = np.array([yr in pre for yr in y.index])
    yp, Xp = y.values[m], Y.values[m, :]
    J = Xp.shape[1]
    pen = np.sum((xt[:, None] - Xd) ** 2, axis=0) if lam > 0 else np.zeros(J)
    obj = lambda w: np.sum((yp - Xp @ w) ** 2) + lam * np.dot(w, pen)
    res = minimize(obj, np.full(J, 1 / J), method="SLSQP", bounds=[(0, 1)] * J,
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                   options={"maxiter": 2000, "ftol": 1e-12})
    return pd.Series(res.x, index=Y.columns), bool(res.success)


def fit(df, dv, treated, donors, lam=0.0, penalized_pool=False):
    y, Y = outcome_matrices(df, dv, treated, donors)
    xt = Xd = None
    if penalized_pool or lam > 0:
        xt, Xd, keep = covariate_vectors(df, treated, list(Y.columns))
        Y = Y[keep]
    w, ok = weights(y, Y, PRE, xt, Xd, lam)
    syn = Y.values @ w.values
    gap = pd.Series(y.values - syn, index=y.index)
    pre_rmse = float(np.sqrt((gap[gap.index < T_YEAR] ** 2).mean()))
    post = gap[gap.index >= T_YEAR]
    return {"y": y, "syn": pd.Series(syn, index=y.index), "gap": gap, "w": w, "ok": ok,
            "pre_rmse": pre_rmse, "post_gap": float(post.mean()), "post_abs": float(post.abs().mean()),
            "n_donors": Y.shape[1]}


# ----------------------------------------------------------------- pieces
def structural_ranking(df):
    m = df[df.year.isin(PRE)].groupby("iso3")[COVARS].mean().dropna()
    z = (m - m.mean()) / m.std(ddof=0)
    d = np.sqrt(((z - z.loc[TREATED]) ** 2).sum(axis=1)).drop(TREATED).sort_values()
    t = pd.DataFrame({"iso3": d.index, "rank": range(1, len(d) + 1), "distance": d.values})
    t["brics_status"] = np.select([t.iso3.isin(BRICS_MEMBERS), t.iso3.isin(BRICS_INVITED),
                                   t.iso3.isin(BRICS_PARTNERS)], ["member", "invited", "partner"], "")
    save_table(t.round(4), "structural_ranking")
    record("rank1", t.iso3.iloc[0]); record("rank1_dist", t.distance.iloc[0])
    record("ranking_n", len(t))
    pool, top = set(t.iso3), set(t.iso3.head(10))
    rows = []
    for lab, S in [("members only", BRICS_MEMBERS),
                   ("members + invited (SAU, TUR)", BRICS_MEMBERS | BRICS_INVITED),
                   ("members + invited + partners", BRICS_MEMBERS | BRICS_INVITED | BRICS_PARTNERS)]:
        K, k = len(S & pool), len(S & top)
        rows.append({"definition": lab, "K_in_pool": K, "N_pool": len(pool), "hits_top10": k,
                     "p_hypergeom": hypergeom.sf(k - 1, len(pool), K, 10)})
    h = pd.DataFrame(rows)
    save_table(h, "brics_hypergeometric")
    print(t.head(10).to_string(index=False)); print(h.to_string(index=False))
    record("brics_members_top10", int(h.iloc[0].hits_top10))
    record("brics_p_members", float(h.iloc[0].p_hypergeom))


def lambda_sweep(df, outcomes, plt):
    rows, cv_rows, store = [], [], {}
    for dv in outcomes:
        donors = get_donors(df, dv)
        for lam in LAMBDAS:
            r = fit(df, dv, TREATED, donors, lam, penalized_pool=True)
            top = r["w"][r["w"] > 0.01].sort_values(ascending=False)
            rows.append({"outcome": dv, "lambda": lam, "pre_rmse": r["pre_rmse"],
                         "post_gap": r["post_gap"], "n_donors_pool": r["n_donors"],
                         "n_weight_ge_1pct": len(top), "converged": r["ok"],
                         "top3": ", ".join(f"{c} ({v:.0%})" for c, v in top.head(3).items())})
            store[(dv, lam)] = r["w"]
        # leave-one-pre-year-out CV (paper's procedure)
        y, Y = outcome_matrices(df, dv, TREATED, donors)
        xt, Xd, keep = covariate_vectors(df, TREATED, list(Y.columns)); Y = Y[keep]
        for lam in LAMBDAS:
            errs = []
            for h in PRE:
                w, _ = weights(y, Y, [p for p in PRE if p != h], xt, Xd, lam)
                errs.append((y.loc[h] - float(Y.loc[h] @ w)) ** 2)
            cv_rows.append({"outcome": dv, "lambda": lam, "cv_mse": float(np.mean(errs))})
    t, cv = pd.DataFrame(rows), pd.DataFrame(cv_rows)
    save_table(t.round(4), "scm_lambda_sweep"); save_table(cv.round(6), "scm_lambda_cv")
    print(t.drop(columns="n_donors_pool").round(4).to_string(index=False))
    for dv in outcomes:
        c = cv[cv.outcome == dv]
        record(f"cv_lambda_{dv}", float(c.loc[c.cv_mse.idxmin(), "lambda"]))
        s = t[t.outcome == dv].set_index("lambda")
        record(f"sweep_{dv}_gap_l0", s.loc[0.0, "post_gap"]); record(f"sweep_{dv}_rmse_l0", s.loc[0.0, "pre_rmse"])
        record(f"sweep_{dv}_gap_l1", s.loc[1.0, "post_gap"]); record(f"sweep_{dv}_gap_l100", s.loc[100.0, "post_gap"])

    # figure 1: gap and pre-RMSE in separate rows (no dual axis)
    fig, axes = plt.subplots(2, len(outcomes), figsize=(5.6 * len(outcomes), 6.2),
                             sharex=True, squeeze=False)
    xs = np.array([1e-3 if l == 0 else l for l in LAMBDAS])
    for j, dv in enumerate(outcomes):
        s = t[t.outcome == dv]
        opt = cv[cv.outcome == dv].sort_values("cv_mse").iloc[0]["lambda"]
        for i, (col, lab, colr) in enumerate([("post_gap", "Post-2022 mean gap", BLUE),
                                              ("pre_rmse", "Pre-period RMSE", ORANGE)]):
            ax = axes[i, j]
            ax.semilogx(xs, s[col], "o-", color=colr, ms=7)
            ax.axvline(1e-3 if opt == 0 else opt, color=INK2, ls=":", lw=1.3)
            ax.set_ylabel(lab)
            if col == "post_gap":
                ax.axhline(0, color=INK2, lw=0.8)
                ax.set_title(OUTCOMES[dv], fontsize=11.5)
                ax.text(0.03, 0.15, f"dotted line: CV optimum λ = {opt:g}",
                        transform=ax.transAxes, ha="left", fontsize=9, color=INK2)
        for ax in axes[:, j]:
            ax.set_xticks(xs); ax.set_xticklabels([f"{l:g}" for l in LAMBDAS]); ax.minorticks_off()
        axes[1, j].set_xlabel("Penalty λ (log spacing; 0 plotted at the left edge)")
    save_fig(fig, "fig_scm_lambda_sweep")

    # figure 2: donor composition by lambda (stacked, fixed colours per donor)
    fig, axes = plt.subplots(1, len(outcomes), figsize=(5.6 * len(outcomes), 4.2), squeeze=False)
    named = ["IDN", "TUR", "EGY", "LKA", "MDV"]
    colors = {"IDN": BLUE, "TUR": ORANGE, "EGY": AQUA, "LKA": "#eda100", "MDV": "#4a3aa7",
              "Other": MUTED}
    for j, dv in enumerate(outcomes):
        ax = axes[0, j]
        base = np.zeros(len(LAMBDAS))
        for c in named + ["Other"]:
            v = np.array([(store[(dv, l)].drop(named, errors="ignore").sum() if c == "Other"
                           else store[(dv, l)].get(c, 0.0)) for l in LAMBDAS])
            ax.bar(range(len(LAMBDAS)), v, bottom=base, color=colors[c], label=c,
                   edgecolor="white", linewidth=1.5, width=0.7)
            base += v
        ax.set_xticks(range(len(LAMBDAS))); ax.set_xticklabels([f"{l:g}" for l in LAMBDAS])
        ax.set_xlabel("λ"); ax.set_ylabel("Donor weight"); ax.set_ylim(0, 1.02)
        ax.set_title(OUTCOMES[dv], fontsize=11.5); ax.grid(axis="x", visible=False)
    axes[0, -1].legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    save_fig(fig, "fig_scm_donor_weights")


def informativeness(df, outcomes):
    rows = []
    for dv in outcomes:
        donors = get_donors(df, dv)
        pre = df[df.iso3.isin(donors) & df.year.isin(PRE)]
        nun = pre.groupby("iso3")[dv].nunique()
        rows.append({"outcome": dv, "donors": len(donors), "constant_pre": int((nun <= 1).sum()),
                     "informative": int((nun > 1).sum()),
                     "max_naive_p_if_flat_never_exceed": (nun > 1).sum() / len(donors)})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "scm_donor_informativeness")
    for _, r in t.iterrows():
        record(f"flat_donors_{r.outcome}", int(r.constant_pre)); record(f"donors_{r.outcome}", int(r.donors))
    return t


def placebo(df, dv, lam, donors_pool, penalized_pool):
    """In-space placebo: mean |post gap| of each donor treated as fake Russia."""
    gaps = {}
    for fake in donors_pool:
        others = [d for d in donors_pool if d != fake]
        try:
            r = fit(df, dv, fake, others, lam, penalized_pool)
            gaps[fake] = r["post_abs"]
        except Exception:
            pass
    return gaps


def inference(df, outcomes):
    rows = []
    for dv, lam, pen in [("bmp_premium_arcsinh", 0.0, False), ("rmb_settlement_proxy_it", 0.0, False),
                         ("bmp_premium_arcsinh", 1.0, True)]:
        if dv not in outcomes or (Opts.fast and lam > 0):
            continue
        donors = get_donors(df, dv)
        r = fit(df, dv, TREATED, donors, lam, penalized_pool=pen)
        pool = list(r["w"].index)
        g = placebo(df, dv, lam, pool, pen)
        nun = df[df.iso3.isin(pool) & df.year.isin(PRE)].groupby("iso3")[dv].nunique()
        inf = set(nun[nun > 1].index)
        for lab, sub in [("all donors (paper)", g), ("informative donors only",
                                                     {k: v for k, v in g.items() if k in inf})]:
            n_ext = sum(v >= r["post_abs"] for v in sub.values())
            rows.append({"outcome": dv, "lambda": lam, "pool": lab, "N": len(sub), "n_exceed": n_ext,
                         "p_paper (n/N)": n_ext / len(sub) if sub else np.nan,
                         "p_(n+1)/(N+1)": (n_ext + 1) / (len(sub) + 1),
                         "russia_post_abs_gap": r["post_abs"],
                         "exceeding": ", ".join(sorted(k for k, v in sub.items() if v >= r["post_abs"]))})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "scm_placebo_inference")
    print(t.round(4).to_string(index=False))
    for _, x in t.iterrows():
        key = f"placebo_{x.outcome}_l{x['lambda']:g}_{'all' if x.pool.startswith('all') else 'inf'}"
        record(key, float(x["p_paper (n/N)"]))


def settlement_forensics(df):
    if not {"china_trade_share_it", "swift_rmb_global_pct"} <= set(df.columns):
        return
    d = df.dropna(subset=["rmb_settlement_proxy_it"]).copy()
    d["product"] = d.china_trade_share_it * d.swift_rmb_global_pct / 100
    both = d.dropna(subset=["product"])
    corr = float(both[["rmb_settlement_proxy_it", "product"]].corr().iloc[0, 1])
    zeros = d[d.rmb_settlement_proxy_it == 0]
    share_missing = float(zeros.china_trade_share_it.isna().mean()) if len(zeros) else np.nan
    record("settle_corr_with_product", corr); record("settle_zero_trade_missing_share", share_missing)
    r = df[(df.iso3 == "RUS") & (df.year >= 2016)][["year", "rmb_settlement_proxy_it",
                                                     "china_trade_share_it", "swift_rmb_global_pct"]]
    save_table(r.round(4), "settlement_proxy_forensics")
    print(f"    settlement proxy vs (China share x SWIFT RMB / 100): corr = {corr:.3f}; "
          f"zeros with China share missing = {share_missing:.1%}")
    print(r.round(3).to_string(index=False))


def scm_figures(df, outcomes, plt):
    fits = {}
    for dv in [o for o in OUTCOMES if o in outcomes]:
        fits[dv] = fit(df, dv, TREATED, get_donors(df, dv), 0.0)

    def panel(ax, dv, title, note=None):
        r = fits[dv]
        ax.plot(r["y"].index, r["y"].values, "o-", color=RED, ms=6, label="Russia")
        ax.plot(r["syn"].index, r["syn"].values, "s--", color=BLUE, ms=5, label="Synthetic Russia")
        ax.axvline(T_YEAR - 0.5, color=INK2, ls=":", lw=1.2)
        ax.set_title(title, fontsize=11.5)
        ax.text(0.03, 0.95, f"Pre-RMSE = {r['pre_rmse']:.3f}", transform=ax.transAxes,
                va="top", fontsize=9, color=INK2)
        if note:
            ax.text(0.03, 0.80, note, transform=ax.transAxes, va="top", fontsize=9, color=INK)
        ax.set_xlabel("Year")

    show = [o for o in ("bmp_premium_arcsinh", "clearing_bank_it") if o in fits]
    bmp_note = ""
    if "bmp_premium_arcsinh" in fits:
        dn = get_donors(df, "bmp_premium_arcsinh")
        nun = df[df.iso3.isin(dn) & df.year.isin(PRE)].groupby("iso3")["bmp_premium_arcsinh"].nunique()
        bmp_note = f"{int((nun <= 1).sum())} of {len(dn)} donors constant pre-2022"
    if show:
        fig, axes = plt.subplots(1, len(show), figsize=(6 * len(show), 4.3), squeeze=False)
        ttl = {"bmp_premium_arcsinh": ("(a) Black-market FX premium (arcsinh) — descriptive", bmp_note),
               "clearing_bank_it": (f"({'b' if len(show) == 2 else 'a'}) Clearing-bank indicator — capacity intact",
                                    "Constant series: no gap by design")}
        for ax, dv in zip(axes[0], show):
            panel(ax, dv, *ttl[dv])
        axes[0, 0].set_ylabel("Outcome value"); axes[0, 0].legend(loc="center left")
        save_fig(fig, "fig_scm_bmp_clearing")
    if len(fits) == 3:
        fig, axes = plt.subplots(1, 3, figsize=(17, 4.3))
        panel(axes[0], "bmp_premium_arcsinh", "(a) Black-market FX premium (arcsinh)")
        panel(axes[1], "rmb_settlement_proxy_it", "(b) SWIFT-observable RMB settlement proxy",
              "RUS 2022–23 = 0 because China-trade\nshare is missing (not an observed collapse)")
        panel(axes[2], "clearing_bank_it", "(c) Clearing-bank indicator (falsification)")
        axes[0].legend(loc="center left")
        save_fig(fig, "fig_scm_three_outcomes")


def run():
    banner("S04  PART III - penalized synthetic control (Russia 2022)")
    plt = setup_style()
    path = Opts.panel_full or Opts.panel
    df = pd.read_csv(path, low_memory=False)
    outcomes = [o for o in OUTCOMES if o in df.columns]
    if "bmp_premium_arcsinh" not in outcomes:
        print(f"    {path.name} has no bmp_premium_arcsinh -> BMP parts skipped "
              "(pass --panel-full MASTER_PANEL_v25b_clean.csv)")
    structural_ranking(df)
    sweep = [o for o in ("bmp_premium_arcsinh", "rmb_settlement_proxy_it") if o in outcomes]
    lambda_sweep(df, sweep, plt)
    informativeness(df, sweep)
    inference(df, sweep)
    settlement_forensics(df)
    scm_figures(df, outcomes, plt)


if __name__ == "__main__":
    run()
