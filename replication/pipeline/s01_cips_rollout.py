"""Part I - CIPS accession and clearing-bank adoption (paper Sections 5.1-5.2).

Outputs
  tables/cips_infrastructure_twfe.csv          paper Table 6 (TWFE baseline / group trend)
  tables/placebo_cips_t3.csv              paper Table 11 placebo rows (v29 spec)
  tables/rollout_timing_clearing_vs_cips.csv               clearing-bank year vs CIPS-accession year
  tables/csdid_sensitivity.csv            CS-DiD: manual (paper) vs bootstrap aggregation
  tables/csdid_dynamic.csv                CS-DiD dynamic ATT(e), bootstrap SEs
  figures/fig_event_study_clearing_bank                 event study (paper Figure 1, units relabelled)
  figures/fig_csdid_dynamic_anticipation               CS-DiD dynamic: no anticipation vs 2-yr anticipation
"""
from __future__ import annotations

import contextlib
import io

import numpy as np
import pandas as pd

from .common import (CS, FE, INK2, MUTED, ORANGE, BLUE, Opts, banner, coef,
                     fit_twfe, load_panel, record, save_fig, save_table,
                     setup_style)


# --------------------------------------------------------------------------
def table6(df):
    rows = []
    for dv, lab in [("clearing_bank_it", "Clearing bank (0/1)"),
                    ("swap_line_it", "Swap line (0/1)"),
                    ("rmb_infra_it", "RMB infra index (0-2)")]:
        ma = fit_twfe(df, f"{dv} ~ CIPSit + {CS}{FE}")
        mb = fit_twfe(df, f"{dv} ~ CIPSit + trend_direct + {CS}{FE}")
        rows += [{"dv": lab, "spec": "(A) Baseline", "var": "CIPSit", **coef(ma, "CIPSit")},
                 {"dv": lab, "spec": "(B) + Group trend", "var": "CIPSit", **coef(mb, "CIPSit")},
                 {"dv": lab, "spec": "(B) + Group trend", "var": "trend_direct",
                  **coef(mb, "trend_direct")}]
    t = pd.DataFrame(rows)
    save_table(t.round(4), "cips_infrastructure_twfe")
    cb = t[t.dv.str.startswith("Clearing")]
    record("t6_clear_base", cb.iloc[0].beta)
    record("t6_clear_trend", cb.iloc[1].beta)
    record("t6_clear_trend_p", cb.iloc[1].p)
    record("t6_clear_trend_slope", cb.iloc[2].beta)
    sw = t[t.dv.str.startswith("Swap")]
    record("t6_swap_base", sw.iloc[0].beta)
    record("t6_swap_trend", sw.iloc[1].beta)
    return t


# --------------------------------------------------------------------------
def event_study(df, plt):
    """Replicates the paper's event study (clip [-5, 7], reference t = -1)."""
    d = df.copy()
    et = np.where(d["g_first_treat"].notna(), d["year"] - d["g_first_treat"], np.nan)
    d["et"] = pd.Series(et, index=d.index).clip(-5, 7)
    vals = sorted(int(v) for v in d["et"].dropna().unique() if v != -1)
    cols = []
    for v in vals:
        c = f"Em{abs(v)}" if v < 0 else ("E0" if v == 0 else f"Ep{v}")
        d[c] = (d["et"] == v).astype(float)
        d.loc[d["et"].isna(), c] = 0.0
        cols.append(c)
    m = fit_twfe(d, "clearing_bank_it ~ " + " + ".join(cols) + f" + {CS}{FE}")
    ci = m.conf_int().loc[cols]
    es = pd.DataFrame({"t": vals, "coef": m.params[cols].values,
                       "lo": ci.iloc[:, 0].values, "hi": ci.iloc[:, 1].values})
    pre = es[es.t <= -2]
    slope, icpt = np.polyfit(pre.t, pre.coef, 1)
    shift = float(es.loc[es.t == 0, "coef"].iloc[0] - icpt)
    record("es_pretrend_slope", slope)
    record("es_level_shift", shift)
    save_table(es.round(4), "event_study_clearing_bank_coefs")

    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.axvspan(-2.5, -0.5, color=ORANGE, alpha=0.08, lw=0)
    ax.text(-1.5, 0.30, "anticipation\nwindow", ha="center", va="top",
            fontsize=9, color=INK2)
    ax.fill_between(es.t, es.lo, es.hi, color=BLUE, alpha=0.12, lw=0)
    ax.errorbar(es.t, es.coef, yerr=[es.coef - es.lo, es.hi - es.coef], fmt="o-",
                color=BLUE, capsize=3, ms=7, lw=2, label="Event-study coefficient (95% CI)")
    xt = np.linspace(-5, 2, 50)
    ax.plot(xt, slope * xt + icpt, "--", color=MUTED, lw=1.5,
            label=f"Pre-trend extrapolation ({slope * 100:.1f} pp / yr)")
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(-0.5, color=INK2, ls=":", lw=1.2)
    y0 = float(es.loc[es.t == 0, "coef"].iloc[0])
    ax.annotate(f"Level shift above trend: +{shift * 100:.0f} pp",
                xy=(0, y0), xytext=(2.4, 0.27), fontsize=10,
                arrowprops=dict(arrowstyle="->", color=INK2, lw=1.2))
    ax.set_ylim(top=0.32)
    ax.set_xlabel("Event time (0 = CIPS accession year)")
    ax.set_ylabel("Clearing-bank probability\nrelative to t = −1")
    ax.set_title("Event study: clearing-bank adoption around CIPS accession")
    ax.legend(loc="lower right")
    save_fig(fig, "fig_event_study_clearing_bank")
    return es


# --------------------------------------------------------------------------
def placebo_t3(df):
    """Paper Table 11 placebo rows (v29 cell 15): no group trend."""
    plc = df.copy()
    plc["CIPS_placebo"] = (plc["g_first_treat"].notna() &
                           (plc["year"] >= plc["g_first_treat"] - 3)).astype(float)
    plc = plc[plc["g_first_treat"].isna() | (plc["year"] < plc["g_first_treat"])]
    rows = []
    for dv in ["clearing_bank_it", "rmb_invoicing_w"]:
        m = fit_twfe(plc, f"{dv} ~ CIPS_placebo + {CS}{FE}")
        rows.append({"dv": dv, **coef(m, "CIPS_placebo")})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "placebo_cips_t3")
    record("placebo_t3_clear", t.iloc[0].beta)
    record("placebo_t3_inv", t.iloc[1].beta)
    record("placebo_t3_inv_p", t.iloc[1].p)


# --------------------------------------------------------------------------
def rollout_timing(df):
    c = df[df.CIPSit == 1].groupby("iso3").year.min()
    b = df[df.clearing_bank_it >= 0.5].groupby("iso3").year.min()
    s = df[df.swap_line_it >= 0.5].groupby("iso3").year.min()
    t = pd.DataFrame({"cips_year": c, "clearing_bank_year": b, "swap_line_year": s}).loc[c.index]
    t["clear_minus_cips"] = t.clearing_bank_year - t.cips_year
    t = t.reset_index().rename(columns={"index": "iso3"}).sort_values("clear_minus_cips")
    save_table(t, "rollout_timing_clearing_vs_cips")
    k = t.clear_minus_cips.dropna()
    record("timing_n_joiners", int(len(t)))
    record("timing_with_clearing", int(len(k)))
    record("timing_before", int((k < 0).sum()))
    record("timing_same", int((k == 0).sum()))
    record("timing_after", int((k > 0).sum()))
    print(f"    CIPS joiners with a clearing bank: {len(k)} of {len(t)} | "
          f"before {(k < 0).sum()}, same year {(k == 0).sum()}, after {(k > 0).sum()}")


# --------------------------------------------------------------------------
def csdid_all(df, plt):
    try:
        from csdid.att_gt import ATTgt
    except ImportError:
        print("    csdid not installed -> skipping CS-DiD (pip install csdid==0.4.2)")
        return
    cs = df[["iso3", "year", "clearing_bank_it", "g_first_treat"]].copy()
    cs["g"] = cs["g_first_treat"].fillna(0).astype(int)
    cs["id"] = cs["iso3"].map({k: i for i, k in enumerate(cs["iso3"].unique())})
    cs = cs.dropna(subset=["clearing_bank_it"])
    B = 199 if Opts.fast else 999

    def fit(**kw):
        np.random.seed(Opts.seed)          # att_gt cell SEs are bootstrap-based -> fix the seed
        m = ATTgt(data=cs, yname="clearing_bank_it", tname="year", idname="id",
                  gname="g", **kw)
        with contextlib.redirect_stdout(io.StringIO()):
            return m.fit(est_method="dr")

    def agg(r, typ):
        np.random.seed(Opts.seed)
        with contextlib.redirect_stdout(io.StringIO()):
            r.aggte(typec=typ, bstrap=True, biters=B)
        a = r.atte
        return a

    # (1) paper's manual aggregation (v24 cell 7): treats ATT(g,t) as independent
    r0 = fit(control_group=["nevertreated"])
    res = r0.results
    gt = pd.DataFrame({"g": res["group"], "t": res["year"], "att": res["att"], "se": res["se"]})
    n_g = cs[cs.g > 0].groupby("g").id.nunique()
    gt["n"] = gt.g.map(n_g)
    post = gt[(gt.t >= gt.g) & gt.se.notna()]
    man_att = float(np.average(post.att, weights=post.n))
    man_se = float(np.sqrt(np.average(post.se ** 2, weights=post.n ** 2)
                           / post.n.sum() ** 2 * (post.n ** 2).sum()))
    record("csdid_manual_att", man_att)
    record("csdid_manual_se", man_se)

    rows = [{"spec": "Paper: manual aggregation (cells independent)",
             "control": "never", "anticipation": 0, "att": man_att, "se": man_se}]
    dyn_store = {}
    for ctrl, ant in [("nevertreated", 0), ("notyettreated", 0),
                      ("nevertreated", 1), ("nevertreated", 2), ("notyettreated", 2)]:
        r = fit(control_group=[ctrl], anticipation=ant)
        a = agg(r, "simple")
        att, se = float(a["overall_att"]), float(np.ravel(a["overall_se"])[0])
        rows.append({"spec": "Bootstrap aggregation (influence function)",
                     "control": ctrl.replace("treated", ""), "anticipation": ant,
                     "att": att, "se": se})
        if ctrl == "nevertreated" and ant in (0, 2):
            d = agg(r, "dynamic")
            dyn_store[ant] = pd.DataFrame({"e": np.ravel(d["egt"]),
                                           "att": np.ravel(d["att_egt"]),
                                           "se": np.ravel(d["se_egt"])})
    t = pd.DataFrame(rows)
    t["ci_lo"], t["ci_hi"] = t.att - 1.96 * t.se, t.att + 1.96 * t.se
    t["p_normal"] = 2 * (1 - __import__("scipy").stats.norm.cdf((t.att / t.se).abs()))
    save_table(t.round(4), "csdid_sensitivity")
    print(t.round(4).to_string(index=False))
    record("csdid_boot_att_a0", t.iloc[1].att)
    record("csdid_boot_se_a0", t.iloc[1].se)
    record("csdid_boot_att_a2", t.iloc[4].att)
    record("csdid_boot_se_a2", t.iloc[4].se)

    dyn = pd.concat([v.assign(anticipation=k) for k, v in dyn_store.items()])
    dyn = dyn[dyn.se.notna()]
    save_table(dyn.round(4), "csdid_dynamic")

    fig, ax = plt.subplots(figsize=(10, 5))
    for k, col, lab, off in [(0, BLUE, "No anticipation (paper)", -0.12),
                             (2, ORANGE, "2-year anticipation (base t−3)", 0.12)]:
        d = dyn[dyn.anticipation == k]
        ax.errorbar(d.e + off, d.att, yerr=1.96 * d.se, fmt="o-", color=col,
                    capsize=3, ms=7, lw=2, label=lab)
    ax.axhline(0, color=INK2, lw=0.8)
    ax.axvline(-0.5, color=INK2, ls=":", lw=1.2)
    ax.set_xlabel("Event time (0 = CIPS accession year)")
    ax.set_ylabel("ATT on clearing-bank probability")
    ax.set_title("Callaway–Sant'Anna dynamic effects (bootstrap 95% CI)")
    ax.legend(loc="upper left")
    save_fig(fig, "fig_csdid_dynamic_anticipation")


# --------------------------------------------------------------------------
def run():
    banner("S01  PART I - CIPS accession and clearing-bank adoption")
    plt = setup_style()
    df = load_panel()
    table6(df)
    event_study(df, plt)
    placebo_t3(df)
    rollout_timing(df)
    csdid_all(df, plt)


if __name__ == "__main__":
    run()
