# The Sanctions Paradox: Financial Sanctions, Payment Rails, and Currency Diversification

*Evidence from Staggered Difference-in-Differences and Penalized Synthetic Control*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Notebook-Jupyter-orange)](https://jupyter.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

This repository contains the data, the original analysis notebook and a scripted replication pipeline for the working paper above. The pipeline regenerates every table and figure from a single command and checks each number against the value printed in the paper.

---

## Overview

Financial sanctions are designed to cut a target off from the dollar payment network. Whether they also move the target *away from the dollar* depends on whether an alternative payment rail exists. The paper formalizes this as the **Sanctions Paradox**:

- Where no alternative infrastructure exists, sanctions **reinforce** dollar use.
- Where alternative infrastructure exists, sanctions **erode** dollar use.
- The switch between the two happens at a threshold level of infrastructure, and that threshold can be estimated.

The evidence comes from a balanced panel of **170 countries, 2010–2023** (2,380 country-years) and is organized in three parts:

| Part | Question | Design |
|---|---|---|
| I | How was RMB payment infrastructure rolled out? | Staggered CIPS accession: TWFE, event study, Callaway–Sant'Anna |
| II | When do sanctions shift currency choice? | Push × Pull interaction, activation threshold, temporal decomposition |
| III | What happened to Russia after February 2022? | Penalized synthetic control (Abadie–L'Hour 2021) and documented facts |

---

## Conceptual framework

| Force | Mechanism | Empirical proxy |
|---|---|---|
| **Push** | Weaponization of dollar payment infrastructure | GSDB financial-sanctions intensity, normalized to [0, 1] |
| **Pull** | Alternative RMB rails | Infra = clearing bank + PBOC swap line ∈ {0, 1, 2}; CIPS accession is used separately as a staggered treatment |
| **Resist** | Digital reproduction of dollar use (USD stablecoins) | Varies only over time, so it is absorbed by year fixed effects; documented, not identified |

The marginal effect of sanctions on RMB invoicing is

$$\frac{\partial\,\text{RMB invoicing}}{\partial\,\text{Sanctions}} = \alpha_2 + \alpha_3\,\text{Infra}
\quad\Longrightarrow\quad \text{Infra}^* = |\alpha_2| / \alpha_3 .$$

The framework predicts α₂ ≤ 0 (Phase 1, coercive reinforcement) and α₃ > 0 (Phase 2, complementarity). Infra\* is the infrastructure level at which the sign of the sanctions effect flips.

---

## Data

The main panel, `MASTER_PANEL.csv`, covers 170 countries × 2010–2023 and is balanced.

| Variable | Description | Source |
|---|---|---|
| `rmb_invoicing_share` | RMB share of trade invoicing (%); 121 countries, 54% exact zeros | Boz et al. (2025) |
| `clearing_bank_it` | PBOC-designated offshore RMB clearing bank (0/1) | PBOC |
| `swap_line_it` | Active PBOC bilateral swap line (0/1) | PBOC |
| `rmb_infra_it` | `clearing_bank_it + swap_line_it` (0–2) | Constructed |
| `CIPSit` | CIPS direct participant (0/1); cohorts 2015 (8), 2016 (32), 2018 (1), never-treated (129) | CIPS Co. Ltd. |
| `sanction_fin_norm_fixed` | Financial-sanctions intensity (0–1) | Global Sanctions Data Base (Felbermayr et al. 2020) |
| Controls | ln GDP, ln trade openness, financial depth, Chinn–Ito capital openness, GDP growth, inflation (w), FDI/GDP (w), UNGA voting alignment (`unga_align_norm_it`; higher = further from the U.S.) | WDI, Chinn–Ito, Bailey–Strezhnev–Voeten |

Optional inputs are used for Part III. Place them in `data/`:

| File | Content |
|---|---|
| `MASTER_PANEL_v25b_clean.csv` | Full panel including the black-market FX premium and SCM inputs |
| `MASTER_PANEL_v25c_rebuilt.csv` | Panel with China's trade share rebuilt from UN Comtrade mirror data (China as reporter) |
| `swift_rmb_tracker_manual_long.csv` | SWIFT RMB Tracker country ranks, 2015–2025 (observed and interpolated flagged) |

---

## Empirical design

**Part I: infrastructure rollout.** TWFE regressions of clearing-bank, swap-line and composite-infrastructure adoption on CIPS accession, with and without a treated-group linear trend. Then an event study (reference t = −1) and Callaway–Sant'Anna group-time ATTs with never-treated and not-yet-treated controls and 0–2 years of anticipation. Aggregation uses the influence function with 999 multiplier-bootstrap draws.

**Part II: Push × Pull interaction.**
$y_{it} = \alpha_1 \text{Infra}_{it} + \alpha_2 \text{Sanc}_{it} + \alpha_3 (\text{Infra}\times\text{Sanc})_{it} + X_{it}'\gamma + \mu_i + \lambda_t + \varepsilon_{it}$,
with country and year fixed effects, eight controls and country-clustered SEs. The model is estimated:

- with three infrastructure measures (composite index, CIPS, clearing bank) and two outcome transformations (winsorized, arcsinh);
- with a winsorization ladder (95th / 99th / 99.5th / none), log(1+y), a two-part model, two-way clustering and leave-one-cohort-out;
- with leave-one-country-out re-estimation, PPML and IV;
- separately for 2010–21, 2015–21 and 2022–23, with country-bootstrap, within-year permutation and influence diagnostics for the post-2022 window.

**Part III: Russia 2022.** Synthetic control for three outcomes chosen because the framework predicts different signs for them: the black-market FX premium (↑), a SWIFT-observable RMB settlement proxy (↓) and clearing-bank presence (no change; falsification).

- **Donor pool:** 157 countries, excluding UKR, BLR, offshore centres and dollarized economies.
- **Penalized SCM:** a pairwise-discrepancy penalty on five standardized structural covariates; λ is chosen by leave-one-pre-year-out cross-validation.
- **Inference:** in-space placebo, reported both for all donors and for informative donors only.
- **Structural similarity:** a ranking of all countries by distance to Russia, with a hypergeometric test of BRICS over-representation among the nearest peers.

---

## Main results

### Part I: CIPS and clearing banks are rolled out as a package

| Estimator | Estimate (pp) | SE | Note |
|---|---|---|---|
| TWFE baseline | +37.8 | 0.072 | p < 0.001 |
| TWFE + treated-group trend | +17.8 | 0.062 | p = 0.004; differential trend +3.1 pp/yr |
| Event-study level shift at t = 0 | +9.0 | — | above the extrapolated pre-trend (9.9 pp/yr) |
| CS-DiD, no anticipation | +5.2 | 0.045 | 95% CI [−3.7, 14.1] |
| CS-DiD, 2-year anticipation | +38.7 | 0.080 | 95% CI [23.0, 54.4] |

- Pre-trends are flat at t ≤ −3. The rise at t = −2 and −1 reflects institutional preparation before accession.
- Of the 23 CIPS joiners that host a clearing bank, 19 had it designated **before** accession, 3 in the same year and 1 after.
- CIPS, clearing banks and swap lines are therefore treated jointly, which motivates the composite Infra index used in Part II.
- Placebo accession at t−3: RMB invoicing +0.021 (p = 0.868).

### Part II: the sanctions effect changes sign at Infra\* ≈ 0.89

| | α₂ (Sanctions) | α₃ (Infra × Sanctions) | Infra\* |
|---|---|---|---|
| Composite index, winsorized (preferred) | −1.566 (p = 0.015) | **+1.770 (p = 0.006)** | **0.885** (delta-method 95% CI 0.45–1.32) |
| Composite index, arcsinh | −1.083 | +1.221 (p < 0.001) | |
| CIPS / clearing bank | −0.160 / −0.534 | +1.556 / +2.197 | |

N = 1,399 country-years in 112 countries (121 countries have invoicing data; the rest drop out on missing controls).

- **Robustness.** α₃ > 0 under every check:
  - winsorization at 95th / 99th / none: +1.08 / +1.64 / +2.10;
  - extensive margin of a two-part model: +0.753 (p = 0.030);
  - log(1+y); two-way clustering (p = 0.003); dropping any CIPS cohort;
  - leave-one-country-out: positive in 112 / 112 refits and p < 0.05 in 111 / 112. Excluding Russia gives +2.79 (p = 0.095).
- **Disclosed limits.**
  - PPML: the interaction is not significant (functional form).
  - IV: the regional CIPS-share instrument is weak (first-stage F = 1.80).
- **Temporal decomposition.** α₃ is +1.58 in 2010–21, +3.01 in 2015–21 and **+20.8** in 2022–23 (p = 0.018; permutation p < 0.001). The magnitude is imprecise: country-bootstrap 95% CI ≈ [−7.5, +50.6].
  - In the published sample, excluding Argentina (2023 swap-line activation) reverses the post-2022 estimate.

### Part III: Russia 2022

| Outcome | Predicted | Synthetic-control result | Diagnostic | Status |
|---|---|---|---|---|
| Clearing-bank indicator | no change | gap = 0 | constant series | capacity intact (direct observation) |
| Black-market FX premium | ↑ | +1.59; placebo p = 0.026 (λ = 1: +1.95, p = 0.021) | 140 / 157 donors constant pre-2022; p = 0.235 on the 17 informative donors | descriptive |
| SWIFT RMB settlement proxy | ↓ | −0.61; placebo p = 0.070 | proxy equals China trade share × global SWIFT RMB share; Russia 2022–23 trade share missing → 0 | not used for inference |

- **Structural peers.** Russia's nearest peers in the five-covariate space are Indonesia (distance 0.629), Türkiye, Saudi Arabia, Mexico, India, the Philippines, Egypt, Colombia, Iran and Italy.
  - Four are BRICS members and two are invitees. A hypergeometric test counting members only gives p = 0.0003.
- **Observed facts, 2021 → 2023.**
  - China's share of Russian trade (rebuilt series): 15.9% → 19.4% → 28.4%, against a 2010–21 trend of +0.79 pp/yr.
  - RMB invoicing: 1.7% → 10.9% → 29.4%, the highest of all 121 countries in 2023.
  - Russia's SWIFT offshore-RMB rank went from 15th (2016) to 6th (2022), after which Russia no longer appears in the tracker.

---

## Replication audit

The scripted pipeline reproduces the paper's estimates and documents five issues found during replication. Each is reported next to the published value, not in place of it.

1. **CS-DiD standard error.** The published SE of 0.018 combined ATT(g,t) cells as if they were independent. The influence-function bootstrap gives 0.045.
2. **Russia 2022–23 observations.** These drop out of every controlled regression because financial depth is missing. Restoring them by last-observation-carried-forward (the rule already used for Chinn–Ito) gives α₃ = +7.29 and Infra\* = 0.45. The sign pattern is unchanged; the magnitude is sensitive.
   - In this restored sample the post-2022 α₃ is +18.5, and +16.4 (clustered p < 0.001) without Argentina. Its bootstrap interval, [−5.0, 37.9], remains wide.
3. **Black-market FX premium.** Hand-coded for 20 countries and zero-filled elsewhere. As a result, placebo p-values are bounded by the number of informative donors.
4. **RMB settlement proxy.** It is an exact product of two other series, so it is reported for transparency only.
5. **China trade share.** The original series double-counted UN Comtrade rows (customs, mode and partner-2 codes were not filtered). It was rebuilt from mirror data: all 9 external magnitude anchors pass, and the share of implausible year-on-year jumps falls from 16.1% to 5.5%. On the rebuilt series, α₃ separates by China-trade exposure: +1.93 (p = 0.029) for high exposure versus +0.79 (p = 0.353) for low exposure.

---

## Repository structure

```
.
├── README.md
├── LICENSE
├── MASTER_PANEL.csv                       # 170 x 14 balanced panel (required)
├── sanctions_dedollarization_panel.ipynb  # original analysis notebook (paper version)
├── data/                                  # optional inputs for Part III (see Data)
├── replication/
│   ├── run_all.py                         # one-command pipeline
│   ├── install.sh                         # environment setup (+ mirror option)
│   ├── requirements.txt
│   └── pipeline/
│       ├── common.py                      # variable construction, estimators, style
│       ├── s01_cips_rollout.py            # Part I
│       ├── s02_interaction.py             # Part II: interaction, robustness, LOO
│       ├── s03_temporal.py                # Part II: temporal decomposition, Argentina
│       ├── s04_synthetic_control.py       # Part III: (penalized) SCM, structural peers
│       ├── s05_russia_facts.py            # Part III: observed facts, heterogeneity
│       └── s06_verify.py                  # checks every number against the paper
└── output/
    ├── figures/                           # PNG (300 dpi) + PDF
    ├── tables/                            # CSV
    ├── results.json
    └── verification_report.md
```

---

## Replication

```bash
git clone https://github.com/simonanana/Payment-Infrastructure-Financial-Sanctions-and-RMB-Internationalization.git
cd Payment-Infrastructure-Financial-Sanctions-and-RMB-Internationalization/replication

python3.12 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
bash install.sh              # or: bash install.sh mirror   (PyPI mirror for slow connections)

python run_all.py --fresh --out ../output \
  --panel      ../MASTER_PANEL.csv \
  --panel-full ../data/MASTER_PANEL_v25b_clean.csv \
  --rebuilt    ../data/MASTER_PANEL_v25c_rebuilt.csv \
  --tracker    ../data/swift_rmb_tracker_manual_long.csv
```

- **Run time.** About 5–12 minutes; `--fast` reduces bootstrap draws and skips the penalized placebo.
- **Inputs.** Only `--panel` is required. Steps whose optional input is missing are skipped and marked SKIP in the report.
- **Selected steps.** Run individual steps with, for example, `--only s02 s06`.
- **Why `install.sh` exists.** It installs `csdid` with `--no-deps`. The package declares `plotnine` and `twine` as dependencies but never imports them.

`output/verification_report.md` lists every reproduced quantity as PASS / FAIL against the paper, followed by the re-estimated results. The current run reproduces all 54 paper values. The published CS-DiD standard error (0.0173) is reproduced only with a fixed seed, because it is built from bootstrap per-cell SEs; it is superseded by the influence-function SE above.

### Pipeline outputs

| Step | Main outputs |
|---|---|
| s01 | `cips_infrastructure_twfe`, `rollout_timing_clearing_vs_cips`, `csdid_sensitivity`, `fig_event_study_clearing_bank`, `fig_csdid_dynamic_anticipation` |
| s02 | `interaction_six_specs`, `marginal_effects`, `robustness_checks`, `ppml_iv`, `loo_full_sample`, `sample_integrity_russia`, `fig_marginal_effects_threshold`, `fig_loo_interaction` |
| s03 | `temporal_decomposition`, `post2022_inference`, `post2022_loo`, `fig_post2022_argentina_loo` |
| s04 | `structural_ranking`, `brics_hypergeometric`, `scm_lambda_sweep`, `scm_placebo_inference`, `scm_donor_informativeness`, `settlement_proxy_forensics`, `fig_scm_lambda_sweep`, `fig_scm_donor_weights`, `fig_scm_bmp_clearing`, `fig_scm_three_outcomes` |
| s05 | `russia_facts`, `heterogeneity_china_trade`, `fig_russia_trade_invoicing` |
| s06 | `verification_report.md` |

### Implementation notes

- **Variable construction.** Follows the paper notebooks exactly: winsorization of the outcome at the 99.5th percentile (Spec A) and a treated-group linear trend.
- **SCM weights.** Solved with the paper's SLSQP settings, so published values reproduce to four decimals. A convex-QP check (cvxpy, multi-start) gives identical weights.
- **Post-2022 resampling.** Uses an exact dummy-variable OLS whose point estimate is asserted to equal PanelOLS. Draws in which α₃ is not identified are skipped.
- **Figures.** One y-axis per panel; colours are validated for colour-vision deficiency.

### Original notebook

`sanctions_dedollarization_panel.ipynb` is the analysis notebook in the form used for the paper. It reads `master_panel.csv`; on case-sensitive systems (Linux, Colab), either rename the file or set `PANEL_FILE = 'MASTER_PANEL.csv'` in the data-loading cell.

---

## Citation

```bibtex
@unpublished{sanctions_paradox_2026,
  title  = {The Sanctions Paradox: Financial Sanctions, Payment Rails, and Currency
            Diversification --- Evidence from Staggered Difference-in-Differences
            and Penalized Synthetic Control},
  author = {Yihan Guo},
  year   = {2026},
  note   = {Working paper}
}
```

## Keywords

`financial sanctions` · `cross-border payment infrastructure` · `CIPS` · `renminbi internationalization` · `de-dollarization` · `staggered difference-in-differences` · `Callaway–Sant'Anna` · `penalized synthetic control` · `BRICS+` · `replication`

## License

MIT. See [LICENSE](LICENSE).
