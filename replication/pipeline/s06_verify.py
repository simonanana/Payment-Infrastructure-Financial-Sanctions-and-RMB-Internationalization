"""Compare every regenerated number with the value printed in the submitted paper.

Writes output/verification_report.md:
  PASS  - reproduces the paper within tolerance
  FAIL  - does not reproduce (investigate before presenting)
  NEW   - re-estimated / since-submission result (no paper target; reported alongside the paper values)
  SKIP  - step not run (missing optional input)
"""
from __future__ import annotations

from .common import Opts, banner, load_results

# key: (paper value, abs tolerance, description, paper section)
PAPER = {
    "t6_clear_base": (0.3778, 5e-4, "TWFE CIPS -> clearing bank, baseline", "5.1-5.2 CIPS"),
    "t6_clear_trend": (0.1784, 5e-4, "TWFE + group trend", "5.1-5.2 CIPS"),
    "t6_clear_trend_slope": (0.0307, 5e-4, "Differential trend per year", "5.1-5.2 CIPS"),
    "t6_swap_trend": (0.0006, 5e-4, "Swap line, group trend", "5.1-5.2 CIPS"),
    "es_pretrend_slope": (0.0987, 5e-4, "Event-study pre-trend slope", "5.1-5.2 CIPS"),
    "es_level_shift": (0.0898, 5e-4, "Event-study level shift at t=0", "5.1-5.2 CIPS"),
    "csdid_manual_att": (0.0518, 5e-4, "CS-DiD simple ATT (paper aggregation)", "5.1-5.2 CIPS"),
    "csdid_manual_se": (0.0173, 3e-3, "CS-DiD SE, cells treated as independent (bootstrap-cell, seed-dependent)", "5.1-5.2 CIPS"),
    "placebo_t3_clear": (0.2634, 5e-4, "Placebo t-3, clearing bank", "5.1-5.2 CIPS"),
    "placebo_t3_inv": (0.0212, 5e-4, "Placebo t-3, invoicing", "5.1-5.2 CIPS"),
    "timing_before": (19, 0, "Clearing bank before CIPS (of 23)", "5.1-5.2 CIPS"),
    "t7_a2": (-1.5655, 5e-4, "alpha_2 Spec (A)", "5.3 Interaction"),
    "t7_a3": (1.7702, 5e-4, "alpha_3 Spec (A)", "5.3 Interaction"),
    "t7_a3_p": (0.0063, 5e-4, "p(alpha_3)", "5.3 Interaction"),
    "t7_asinh_a3": (1.2214, 5e-4, "alpha_3 arcsinh", "5.3 Interaction"),
    "t7_cips_a3": (1.5559, 5e-4, "alpha_3 CIPS", "5.3 Interaction"),
    "t7_clear_a3": (2.1973, 5e-4, "alpha_3 clearing bank", "5.3 Interaction"),
    "infra_star": (0.885, 2e-3, "Infra* = |a2|/a3", "5.3 Interaction"),
    "rob_w95": (1.0775, 5e-4, "Winsorize 95th", "5.5 / App. C"),
    "rob_w99": (1.6409, 5e-4, "Winsorize 99th", "5.5 / App. C"),
    "rob_extensive": (0.7528, 5e-4, "Extensive margin", "5.5 / App. C"),
    "rob_log1p": (0.9398, 5e-4, "log(1+y)", "5.5 / App. C"),
    "rob_twoway_se": (0.6009, 5e-4, "Two-way clustered SE", "5.5 / App. C"),
    "rob_dropRUSCHN": (2.786, 1e-3, "Drop RUS + CHN", "5.5 / App. C"),
    "rob_minctrl": (6.7926, 5e-4, "FE only", "5.5 / App. C"),
    "rob_loco2015": (2.823, 1e-3, "Drop 2015 cohort", "5.5 / App. C"),
    "ppml_sanc": (14.9513, 1e-2, "PPML sanctions main effect", "5.5 / App. C"),
    "iv_first_stage_F": (1.80, 0.02, "IV first-stage F", "5.5 / App. C"),
    "quad_Q1": (0.036, 1e-3, "Quadrant Q1 mean", "2.3 Quadrants"),
    "quad_Q2": (0.246, 1e-3, "Quadrant Q2 mean", "2.3 Quadrants"),
    "t9_pre": (1.5758, 5e-4, "alpha_3 2010-2021", "5.4 / 6 Temporal"),
    "t9_cips_era": (3.005, 1e-3, "alpha_3 2015-2021", "5.4 / 6 Temporal"),
    "t9_post": (20.8046, 1e-3, "alpha_3 2022-2023", "5.4 / 6 Temporal"),
    "t9_post_n": (188, 0, "N 2022-2023", "5.4 / 6 Temporal"),
    "post_exclARG": (-1.7463, 1e-3, "Post-2022 excl. Argentina", "5.4 / 6 Temporal"),
    "post_dfbeta_ARG": (2.6227, 1e-3, "DFBETA Argentina", "5.4 / 6 Temporal"),
    "post_boot_lo": (-7.98, 2.0, "Bootstrap CI low (seed-dependent)", "5.4 / 6 Temporal"),
    "post_boot_hi": (47.21, 6.0, "Bootstrap CI high (seed-dependent)", "5.4 / 6 Temporal"),
    "rank1_dist": (0.629, 1e-3, "Indonesia distance to Russia", "7.6 Penalized SCM"),
    "ranking_n": (154, 0, "Countries in ranking", "7.6 Penalized SCM"),
    "cv_lambda_bmp_premium_arcsinh": (1.0, 0, "CV lambda, BMP", "7.6 Penalized SCM"),
    "cv_lambda_rmb_settlement_proxy_it": (0.0, 0, "CV lambda, settlement", "7.6 Penalized SCM"),
    "sweep_bmp_premium_arcsinh_gap_l0": (1.5854, 1e-3, "BMP gap lambda=0", "7.3 SCM"),
    "sweep_bmp_premium_arcsinh_rmse_l0": (0.2712, 1e-3, "BMP pre-RMSE lambda=0", "7.3 SCM"),
    "sweep_bmp_premium_arcsinh_gap_l1": (1.9465, 1e-3, "BMP gap lambda=1", "7.3 SCM"),
    "sweep_bmp_premium_arcsinh_gap_l100": (3.0887, 1e-3, "BMP gap lambda=100", "7.3 SCM"),
    "sweep_rmb_settlement_proxy_it_gap_l0": (-0.6090, 1e-3, "Settlement gap lambda=0", "7.3 SCM"),
    "sweep_rmb_settlement_proxy_it_rmse_l0": (0.0692, 1e-3, "Settlement pre-RMSE", "7.3 SCM"),
    "placebo_bmp_premium_arcsinh_l0_all": (0.0255, 1e-3, "BMP placebo p (157 donors)", "7.3 SCM"),
    "placebo_rmb_settlement_proxy_it_l0_all": (0.0701, 1e-3, "Settlement placebo p", "7.3 SCM"),
    "placebo_bmp_premium_arcsinh_l1_all": (0.0211, 1e-3, "BMP penalized placebo p", "7.3 SCM"),
    "flat_donors_bmp_premium_arcsinh": (140, 0, "BMP donors constant pre-2022", "7.3 SCM"),
    "rus_invoicing_2023": (29.353, 1e-2, "Russia RMB invoicing 2023", "7.4 Russia"),
    "rus_china_share_2023": (28.4, 0.1, "Russia China share 2023 (rebuilt)", "7.4 Russia"),
}

NEW = {
    "csdid_boot_att_a0": "CS-DiD ATT, bootstrap aggregation, no anticipation",
    "csdid_boot_se_a0": "  ... bootstrap SE (paper reported 0.018)",
    "csdid_boot_att_a2": "CS-DiD ATT, 2-year anticipation",
    "csdid_boot_se_a2": "  ... bootstrap SE",
    "timing_with_clearing": "CIPS joiners with a clearing bank",
    "infra_star_se": "Delta-method SE of Infra*",
    "sd_sanc_sanctioned": "SD of sanctions among sanctioned obs (paper uses 0.11)",
    "sd_sanc_estimation": "SD of sanctions in estimation sample",
    "loo_spec_A_99.5_pos": "LOO (Spec A): alpha_3 > 0 count",
    "loo_spec_A_99.5_sig05": "LOO (Spec A): p < 0.05 count",
    "loo_spec_A_99.5_n": "LOO (Spec A): refits",
    "loo_spec_A_99.5_noRUS_beta": "LOO (Spec A): excl. Russia alpha_3",
    "loo_spec_A_99.5_noRUS_p": "LOO (Spec A): excl. Russia p",
    "loo_w99_pos": "LOO (99th): alpha_3 > 0 count",
    "loo_w99_sig05": "LOO (99th): p < 0.05 count",
    "post2022_obs_with_invoicing": "Post-2022 obs with invoicing data",
    "post2022_obs_in_regression": "Post-2022 obs in regression",
    "restored_a3": "alpha_3, Russia 2022-23 restored",
    "restored_infra_star": "Infra*, Russia 2022-23 restored",
    "post_perm_p": "Post-2022 permutation p",
    "post_restored_a3": "Post-2022 alpha_3, Russia restored",
    "post_restored_exclARG": "  ... excluding Argentina",
    "post_restored_exclARG_p": "  ... p",
    "brics_members_top10": "BRICS full members in top-10 peers",
    "brics_p_members": "Hypergeometric p (members only)",
    "placebo_bmp_premium_arcsinh_l0_inf": "BMP placebo p, informative donors only",
    "settle_corr_with_product": "Settlement proxy vs China share x SWIFT share (corr)",
    "settle_zero_trade_missing_share": "Proxy zeros where China share is missing",
    "rus_china_pretrend_pp_per_year": "Russia China-share pre-trend (pp/yr)",
    "het_high_99": "alpha_3 high China exposure (99th)",
    "het_low_99": "alpha_3 low China exposure (99th)",
}


def run():
    banner("S06  VERIFY against the submitted paper")
    R = load_results()
    lines = ["# Verification report", "",
             "| Status | Section | Quantity | Paper | Regenerated |", "|---|---|---|---|---|"]
    n = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for k, (target, tol, desc, sec) in PAPER.items():
        if k not in R:
            st, got = "SKIP", "—"
        else:
            got = R[k]
            st = "PASS" if abs(float(got) - float(target)) <= tol else "FAIL"
            got = f"{float(got):.4f}"
        n[st] += 1
        lines.append(f"| {st} | {sec} | {desc} | {target} | {got} |")
    lines += ["", "## Re-estimated / since-submission results (no paper target)", "",
              "| Quantity | Value |", "|---|---|"]
    for k, desc in NEW.items():
        v = R.get(k)
        lines.append(f"| {desc} | {'—' if v is None else (f'{v:.4f}' if isinstance(v, float) else v)} |")
    out = Opts.out / "verification_report.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n  PASS {n['PASS']}  FAIL {n['FAIL']}  SKIP {n['SKIP']}  ->  {out}")
    return n


if __name__ == "__main__":
    run()
