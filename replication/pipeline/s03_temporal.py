"""Part II - temporal decomposition and Argentina (paper Sections 5.4 and 6).

Outputs
  tables/temporal_decomposition.csv            paper Table 9 windows (winsorized + arcsinh)
  tables/post2022_inference.csv         country bootstrap CI, permutation p, published vs Russia-restored
  tables/post2022_loo.csv               post-2022 leave-one-out, published and Russia-restored samples
  figures/fig_post2022_argentina_loo          Argentina timeline + post-2022 LOO, published and Russia-restored samples
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import (CONTROLS, BLUE, INK2, MUTED, ORANGE, RED, SANC, Opts, banner, coef,
                     interaction, load_panel, record, restore_russia, save_fig,
                     save_table, setup_style)


def table9(df):
    rows = []
    for lab, mask in [("2010-2021", df.year <= 2021),
                      ("2015-2021", df.year.between(2015, 2021)),
                      ("2022-2023", df.year >= 2022),
                      ("2010-2023", df.year > 0)]:
        for dv in ("rmb_invoicing_w", "rmb_inv_asinh"):
            m = interaction(df[mask], dv)
            rows.append({"window": lab, "dv": dv, "a2": m.params[SANC],
                         **coef(m, "infra_x_sanction")})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "temporal_decomposition")
    w = t[t.dv == "rmb_invoicing_w"].set_index("window")
    record("t9_pre", w.loc["2010-2021", "beta"]); record("t9_cips_era", w.loc["2015-2021", "beta"])
    record("t9_post", w.loc["2022-2023", "beta"]); record("t9_post_p", w.loc["2022-2023", "p"])
    record("t9_post_n", int(w.loc["2022-2023", "n"]))
    return t


def _design(p2):
    """Complete-case design for the fast dummy-variable TWFE used in resampling."""
    cols = ["rmb_invoicing_w", "rmb_infra_it", SANC, "infra_x_sanction"] + CONTROLS
    d = p2.dropna(subset=cols)
    return d, cols


def fast_a3(d, cols):
    """alpha_3 by OLS with entity + year dummies (identical point estimate to PanelOLS)."""
    X = d[cols[1:]].to_numpy(float)
    E = pd.get_dummies(d["iso3"], dtype=float).to_numpy()
    T = pd.get_dummies(d["year"], drop_first=True, dtype=float).to_numpy()
    Z = np.hstack([X, E, T])
    # alpha_3 is estimable iff dropping its column lowers the rank. Then the
    # minimum-norm lstsq solution gives its unique value even when other controls
    # are absorbed (PanelOLS drops those). Otherwise PanelOLS would drop it -> skip.
    r_full = np.linalg.matrix_rank(Z)
    if np.linalg.matrix_rank(np.delete(Z, 2, axis=1)) == r_full:
        return np.nan
    beta, *_ = np.linalg.lstsq(Z, d[cols[0]].to_numpy(float), rcond=None)
    return float(beta[2])                       # order: infra, sanc, infra_x_sanction, ...


def post_inference(df):
    B = 200 if Opts.fast else 1000
    rng = np.random.default_rng(Opts.seed)
    rows = []
    for lab, dd in [("published", df), ("russia_restored", restore_russia(df))]:
        p2 = dd[dd.year >= 2022].copy()
        b = interaction(p2).params["infra_x_sanction"]
        d, cols = _design(p2)
        assert abs(fast_a3(d, cols) - b) < 1e-6, "fast estimator does not match PanelOLS"
        groups = {c: g for c, g in d.groupby("iso3")}
        cs = np.array(sorted(groups))
        boots = []
        for _ in range(B):                                   # country (cluster) bootstrap
            pick = rng.choice(cs, size=len(cs), replace=True)
            bd = pd.concat([groups[c].assign(iso3=f"{c}_{j}") for j, c in enumerate(pick)])
            boots.append(fast_a3(bd, cols))
        boots = [x for x in boots if np.isfinite(x)]
        perms = []
        yrs = d["year"].to_numpy()
        x = d["infra_x_sanction"].to_numpy().copy()
        for _ in range(B):                                   # within-year permutation (paper)
            xp = x.copy()
            for yr in np.unique(yrs):
                k = np.where(yrs == yr)[0]
                xp[k] = rng.permutation(xp[k])
            perms.append(fast_a3(d.assign(infra_x_sanction=xp), cols))
        perms = np.array([x for x in perms if np.isfinite(x)])
        no_arg = interaction(p2[p2.iso3 != "ARG"])
        rows.append({"sample": lab, "a3": b, "boot_lo": np.percentile(boots, 2.5),
                     "boot_hi": np.percentile(boots, 97.5),
                     "perm_p": float(np.mean(np.abs(perms) >= abs(b))),
                     "a3_excl_ARG": no_arg.params["infra_x_sanction"],
                     "p_excl_ARG": no_arg.pvalues["infra_x_sanction"], "B": B,
                     "n_obs": len(d), "n_countries": len(cs), "B_valid": len(boots)})
    t = pd.DataFrame(rows)
    save_table(t.round(4), "post2022_inference")
    print(t.round(3).to_string(index=False))
    record("post_boot_lo", t.iloc[0].boot_lo); record("post_boot_hi", t.iloc[0].boot_hi)
    record("post_perm_p", t.iloc[0].perm_p)
    record("post_exclARG", t.iloc[0].a3_excl_ARG)
    record("post_restored_a3", t.iloc[1].a3)
    record("post_restored_exclARG", t.iloc[1].a3_excl_ARG)
    record("post_restored_exclARG_p", t.iloc[1].p_excl_ARG)


def post_loo(df):
    out = []
    for lab, d in [("published", df), ("russia_restored", restore_russia(df))]:
        p2 = d[d.year >= 2022]
        m = interaction(p2)
        b0, se0 = m.params["infra_x_sanction"], m.std_errors["infra_x_sanction"]
        used = p2.dropna(subset=["rmb_invoicing_w", "rmb_infra_it", SANC] + CONTROLS)
        for c in sorted(used.iso3.unique()):
            b = interaction(p2[p2.iso3 != c]).params["infra_x_sanction"]
            out.append({"sample": lab, "dropped": c, "beta_excl": b, "dfbeta": (b0 - b) / se0, "full": b0})
    t = pd.DataFrame(out)
    save_table(t.round(4), "post2022_loo")
    a = t[(t["sample"] == "published") & (t.dropped == "ARG")]
    record("post_dfbeta_ARG", float(a.dfbeta.iloc[0]))
    record("post_n_countries", int((t["sample"] == "published").sum()))
    return t


def figure(df, loo, plt):
    arg = df[df.iso3 == "ARG"].sort_values("year")
    fig = plt.figure(figsize=(14, 5.2))
    gs = fig.add_gridspec(2, 3, height_ratios=[2.2, 1], width_ratios=[1.15, 1, 1],
                          hspace=0.12, wspace=0.32)
    a = fig.add_subplot(gs[0, 0])
    a.plot(arg.year, arg.rmb_invoicing_share, "o-", color=BLUE, ms=7)
    a.set_ylabel("RMB invoicing (%)")
    a.set_title("(a) Argentina")
    a.annotate("2023: BOP crisis,\nswap line drawn\n(≈USD 2.7bn IMF repaid in RMB)",
               xy=(2023, arg.rmb_invoicing_share.iloc[-1]), xytext=(2014.6, 1.9), fontsize=9,
               arrowprops=dict(arrowstyle="->", color=INK2))
    a.tick_params(labelbottom=False)
    b = fig.add_subplot(gs[1, 0], sharex=a)
    b.step(arg.year, arg.rmb_infra_it, where="mid", color=ORANGE, label="Infra index (0–2)")
    b.step(arg.year, arg[SANC], where="mid", color=MUTED, label="Sanctions (0–1)")
    b.set_ylim(-0.1, 2.3); b.legend(loc="center right", fontsize=8.5)
    b.set_xticks(range(2010, 2024, 2))
    b.set_xlabel("Year")

    for k, (lab, title) in enumerate([("published", "(b) Post-2022 LOO: published sample"),
                                      ("russia_restored", "(c) LOO: Russia 2022–23 restored")]):
        ax = fig.add_subplot(gs[:, k + 1])
        t = loo[loo["sample"] == lab].sort_values("beta_excl").reset_index(drop=True)
        ax.scatter(t.beta_excl, np.arange(len(t)), s=10, color=BLUE)
        ax.axvline(t.full.iloc[0], color=INK2, ls="--", lw=1.2,
                   label=f"Full: {t.full.iloc[0]:+.1f}")
        ax.axvline(0, color=INK2, lw=0.8)
        for c in ("ARG", "RUS"):
            r = t[t.dropped == c]
            if len(r):
                ax.scatter(r.beta_excl, r.index, s=55, color=RED if c == "ARG" else ORANGE, zorder=4)
                ax.annotate(f"excl. {c}: {r.beta_excl.iloc[0]:+.1f}",
                            xy=(r.beta_excl.iloc[0], r.index[0]),
                            xytext=(6, -2 if c == "ARG" else 6), textcoords="offset points", fontsize=9)
        ax.set_yticks([]); ax.set_xlabel("Post-2022 α₃ excluding one country")
        ax.set_title(title, fontsize=11.5); ax.legend(loc="upper left")
    save_fig(fig, "fig_post2022_argentina_loo")


def run():
    banner("S03  PART II - temporal decomposition, Argentina, Russia-restored sample")
    plt = setup_style()
    df = load_panel()
    table9(df)
    post_inference(df)
    loo = post_loo(df)
    figure(df, loo, plt)


if __name__ == "__main__":
    run()
