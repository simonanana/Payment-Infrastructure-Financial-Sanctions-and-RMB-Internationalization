"""Part III - Russia's observed facts (paper Section 7.4) and China-trade heterogeneity (Appendix A2).

Needs the rebuilt China-trade panel (MASTER_PANEL_v25c_rebuilt.csv, from
pathc/run_10_apply_rebuilt.py) for the trade-share series and the
heterogeneity split; the SWIFT tracker CSV is optional.

Outputs
  tables/russia_facts.csv          China share, RMB invoicing, tracker rank 2016-2023
  tables/heterogeneity_china_trade.csv    alpha_3 by high / low pre-2022 China-trade exposure
  figures/fig_russia_trade_invoicing         (a) China share with pre-trend, (b) RMB invoicing
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .common import (BLUE, INK2, MUTED, ORANGE, RED, Opts, banner, coef,
                     interaction, load_panel, record, save_fig, save_table,
                     setup_style)


def run():
    banner("S05  PART III - Russia facts and China-trade heterogeneity")
    plt = setup_style()
    df = load_panel()
    rus = df[df.iso3 == "RUS"].set_index("year")

    share = None
    if Opts.rebuilt and Opts.rebuilt.exists():
        rb = pd.read_csv(Opts.rebuilt, low_memory=False)
        share = rb[rb.iso3 == "RUS"].set_index("year")["china_trade_share_it"]
    else:
        print("    no --rebuilt panel: China-trade panel and heterogeneity skipped "
              "(the original china_trade_share_it is inflated 2016-18 and must not be plotted)")

    trk = None
    if Opts.tracker and Opts.tracker.exists():
        t = pd.read_csv(Opts.tracker)
        trk = t[(t.iso3 == "RUS") & (t.swift_tracker_obs == 1)].set_index("year")["swift_tracker_rank"]

    yrs = range(2016, 2024)
    facts = pd.DataFrame({"year": list(yrs),
                          "rmb_invoicing_pct": [rus["rmb_invoicing_share"].get(y) for y in yrs],
                          "china_share_rebuilt_pct": [share.get(y) if share is not None else np.nan for y in yrs],
                          "swift_tracker_rank_observed": [trk.get(y) if trk is not None else np.nan for y in yrs]})
    save_table(facts.round(2), "russia_facts")
    print(facts.round(2).to_string(index=False))
    for y in (2021, 2022, 2023):
        record(f"rus_invoicing_{y}", float(rus["rmb_invoicing_share"].get(y)))
        if share is not None:
            record(f"rus_china_share_{y}", float(share.get(y)))

    ncols = 2 if share is not None else 1
    fig, axes = plt.subplots(1, ncols, figsize=(6.2 * ncols, 4.4), squeeze=False)
    k = 0
    if share is not None:
        ax = axes[0, 0]; k = 1
        s = share.dropna()
        pre = s[s.index <= 2021]
        b, a = np.polyfit(pre.index, pre.values, 1)
        record("rus_china_pretrend_pp_per_year", float(b))
        ax.plot(s.index, s.values, "o-", color=BLUE, ms=6, label="China's share of Russia's trade")
        xx = np.arange(2010, 2024)
        ax.plot(xx, a + b * xx, "--", color=MUTED, lw=1.5, label=f"2010–21 trend (+{b:.2f} pp/yr)")
        ax.axvline(2021.5, color=INK2, ls=":", lw=1.2)
        for y in (2021, 2023):
            if y in s.index:
                ax.annotate(f"{s[y]:.1f}%", xy=(y, s[y]), xytext=(-9, 0) if y == 2023 else (0, 10), textcoords="offset points",
                            fontsize=10, ha="right" if y == 2023 else "center", va="center" if y == 2023 else "bottom", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
        ax.set_ylabel("% of total trade"); ax.set_xlabel("Year")
        ax.set_title("(a) China's share of Russian trade (rebuilt)", fontsize=11.5)
        ax.legend(loc="upper left")
    ax = axes[0, k]
    inv = rus["rmb_invoicing_share"].dropna()
    ax.plot(inv.index, inv.values, "o-", color=ORANGE, ms=6, label="Russia")
    others = df[(df.iso3 != "RUS")].groupby("year")["rmb_invoicing_share"].median()
    ax.plot(others.index, others.values, "-", color=MUTED, lw=1.5, label="Median, other countries")
    ax.axvline(2021.5, color=INK2, ls=":", lw=1.2)
    for y in (2021, 2022, 2023):
        ax.annotate(f"{inv[y]:.1f}%", xy=(y, inv[y]), xytext=(-9, 0) if y == 2023 else (-9, 4),
                    textcoords="offset points", fontsize=10, ha="right", va="center" if y == 2023 else "bottom", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    ax.set_ylabel("RMB share of trade invoicing (%)"); ax.set_xlabel("Year")
    ax.set_title(f"({'b' if k else 'a'}) RMB invoicing, Russia", fontsize=11.5)
    ax.legend(loc="upper left")
    save_fig(fig, "fig_russia_trade_invoicing")

    # ---- heterogeneity by pre-2022 China-trade exposure (rebuilt series)
    if share is None:
        return
    ct = rb[rb.year <= 2021].groupby("iso3")["china_trade_share_it"].mean().dropna()
    med = ct.median()
    rows = []
    for q, ql in [(0.995, "paper spec (99.5th)"), (0.99, "99th")]:
        d = df.assign(yq=df.rmb_invoicing_share.clip(upper=df.rmb_invoicing_share.quantile(q)))
        for lab, isos in [("High exposure", ct[ct >= med].index), ("Low exposure", ct[ct < med].index)]:
            m = interaction(d[d.iso3.isin(isos)], "yq")
            rows.append({"winsor": ql, "group": lab, **coef(m, "infra_x_sanction")})
    h = pd.DataFrame(rows)
    save_table(h.round(4), "heterogeneity_china_trade")
    print(h.round(3).to_string(index=False))
    record("het_high_99", float(h[(h.winsor == "99th") & (h.group == "High exposure")].beta.iloc[0]))
    record("het_low_99", float(h[(h.winsor == "99th") & (h.group == "Low exposure")].beta.iloc[0]))


if __name__ == "__main__":
    run()
