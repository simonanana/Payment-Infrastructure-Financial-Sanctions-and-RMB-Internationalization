# Sanctions, Infrastructure, and De-Dollarization: Panel Evidence on the Push–Pull–Resist Framework

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Notebook-Jupyter-orange)](https://jupyter.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

This repository contains the full empirical analysis code for the working paper:

> **"Sanctions, Infrastructure, and De-Dollarization: Panel Evidence on the Push–Pull–Resist Framework (2010–2023)"**

The paper formalizes the **Sanctions Paradox**: the finding that financial sanctions and dollar-hegemony erosion are not opposing forces but sequential phases of a single, infrastructure-contingent process. Using a balanced panel of **170 countries over 2010–2023** (N = 2,380 country-year observations), the analysis estimates the conditions under which China's cross-border payment infrastructure (CIPS/clearing banks) converts the political risk premium embedded in financial sanctions into observable RMB invoicing diversification.

---

## Theoretical Framework

The international monetary system is modeled as three concurrent structural forces:

| Force | Description | Empirical Proxy |
|-------|-------------|-----------------|
| **Push** | Weaponization of dollar-denominated payment infrastructure through financial sanctions | Normalized financial sanctions intensity |
| **Pull** | Deliberate construction of parallel non-dollar payment architectures (CIPS, clearing banks, swap lines) by China and the BRICS+ bloc | CIPS accession, RMB clearing-bank presence, bilateral swap lines |
| **Resist** | Digital reproduction of dollar hegemony through USD-pegged stablecoins | USD stablecoin penetration |

The central theoretical contribution is the **Sanctions Paradox**: sanctions reinforce dollar usage when RMB infrastructure is absent (Phase 1) but erode it when infrastructure is in place (Phase 2). The 2022 Russia sanctions watershed serves as the empirical trigger for the population-average Phase 1 → Phase 2 mechanism-state transition.


## Key Findings

| Finding | Estimator | Coefficient | p-value |
|---------|-----------|-------------|---------|
| CIPS accession → clearing-bank adoption | CS-DiD (preferred) | +5.2 pp | ≈ 0.04 |
| CIPS accession → clearing-bank adoption | TWFE baseline | +37.8 pp | < 0.001 |
| CIPS accession → clearing-bank adoption | TWFE + group trend | +17.8 pp | < 0.01 |
| Push×Pull interaction (core) | TWFE | α₃ = +1.77 | 0.006 |
| Push×Pull interaction (arcsinh DV) | TWFE | α₃ = +1.22 | < 0.001 |
| Sanctions main effect (no infrastructure) | TWFE | α₂ = −1.57 | 0.015 |
| Phase 2 Push×Pull amplification (post-2022) | TWFE | α₃ = +20.8 | 0.018 |

The Phase 2 interaction coefficient is **7–13× larger** than the pre-2022 estimate, corroborating the two-phase Sanctions Paradox dynamic.


## Methodology

### Econometric Specifications

1. **Two-Way Fixed Effects (TWFE)** — baseline and group-trend-corrected, with entity and time fixed effects, clustered standard errors by country
2. **Event Study** — dynamic treatment effects around CIPS accession (2015–2018 cohorts)
3. **Callaway–Sant'Anna (2021) CS-DiD** — heterogeneity-robust DiD with group-time ATTs; preferred causal estimator
4. **Poisson Pseudo-Maximum Likelihood (PPML)** — count/share outcome robustness
5. **Instrumental Variable (IV)** — regional CIPS adoption share as instrument for individual CIPS accession
6. **Push×Pull Interaction Models** — three infrastructure proxies (RMB infra index, CIPS, clearing bank); two DV transformations (Winsorized share, arcsinh)
7. **Temporal Decomposition** — Pre-2022 (Phase 1) vs. Post-2022 (Phase 2) subsamples

### Identification Strategy

Three sources of quasi-experimental variation are exploited:
- **Staggered CIPS accession** (2015: 8 countries; 2016: 32 countries; 2018: 1 country)
- **Exogenous Russia sanctions shocks** (2014 and 2022)
- **Sender–Target–Observer taxonomy** structuring mechanism transmission and heterogeneity tests

### Controls

GDP (log), trade openness (log), financial depth, capital account openness (Chinn–Ito), GDP growth, inflation (Winsorized), FDI inflows (% GDP, Winsorized), UN General Assembly alignment score.


## Repository Structure

```
.
├── sanctions_dedollarization_panel.ipynb   # Main analysis notebook (all sections)
├── master_panel.csv                        # ⚠ Required: 170-country balanced panel (not included)
├── output/                                 # Generated figures and tables (auto-created)
│   ├── table1_core_cips_infrastructure.csv
│   ├── table2_push_pull_interaction.csv
│   ├── fig_event_study_clearing.png
│   ├── fig_event_study_rmb.png
│   ├── fig_csdid_att.png
│   ├── fig_phase_decomposition.png
│   ├── fig_quadrant.png
│   ├── fig_argentina_deep_dive.png
│   ├── fig_marginal_effects.png
│   ├── fig_permutation_test.png
│   ├── fig_force_composition_integrated.png
│   └── ...
└── README.md
```

---

## Notebook Structure

| Section | Content |
|---------|---------|
| 1 | Environment setup and package installation |
| 2 | Data loading, variable construction, CIPS cohort verification, BRICS+ profiles |
| 3 | Helper functions (TWFE wrapper, table export) |
| 4 | Core regression tables (Table 1: CIPS → Infrastructure; Table 2: Push×Pull) |
| 5 | Event study (dynamic treatment effects) |
| 6 | Callaway–Sant'Anna CS-DiD estimation |
| 7 | PPML robustness |
| 8 | IV estimation (regional CIPS share instrument) |
| 9 | Heterogeneity analysis (subgroup splits and role taxonomy) |
| 10 | Robustness checks (broad CIPS, sample exclusions, DV transforms) |
| 11 | Temporal decomposition + bootstrap amplification ratio CI |
| 12 | All main text figures |
| 13 | Paper statistics verification |
| 14 | Output export summary |
| 15 | Supplementary analyses (Argentina deep dive, marginal effects, permutation inference, placebo test, force composition figure) |


## Data Requirements

The main analysis requires `master_panel.csv` — a balanced country-year panel with the following key variables:

| Variable | Description |
|----------|-------------|
| `iso3` | ISO 3166-1 alpha-3 country code |
| `year` | Year (2010–2023) |
| `CIPSit` | CIPS membership indicator (0/1) |
| `clearing_bank_it` | RMB offshore clearing bank indicator (0/1) |
| `swap_line_it` | PBoC bilateral swap line indicator (0/1) |
| `rmb_infra_it` | RMB infrastructure index (clearing bank + swap line, 0–2) |
| `rmb_invoicing_share` | Cross-border RMB invoicing share (%) |
| `sanction_fin_norm_fixed` | Normalized financial sanctions intensity |
| `ln_gdp` | Log GDP (constant USD) |
| `ln_trade_openness` | Log trade openness |
| `financial_depth_it` | Private credit / GDP |
| `capital_openness_it_filled` | Chinn–Ito capital account openness index |
| `gdp_growth_it` | GDP growth rate |
| `inflation_it_w` | CPI inflation (Winsorized) |
| `fdi_inflow_gdp_it_w` | FDI inflows / GDP (Winsorized) |
| `unga_align_norm_it` | UN General Assembly voting alignment with China |

**Data sources:** BIS Triennial Survey, SWIFT RMB Tracker, PBoC reports, CIPS official disclosures, World Bank WDI, IMF IFS, Chinn–Ito index, UN Comtrade, UNGA voting records, Global Sanctions Database.


## Installation

```bash
pip install pandas numpy scipy matplotlib statsmodels linearmodels
```

Or using conda:

```bash
conda install pandas numpy scipy matplotlib statsmodels
pip install linearmodels
```

The notebook also supports Google Colab — upload `master_panel.csv` to the Colab session storage or mount Google Drive before running.


## Replication

1. Clone the repository
2. Place `master_panel.csv` in the project root
3. Run `sanctions_dedollarization_panel.ipynb` from top to bottom
4. All figures and tables will be saved to `output/`


## Citation

If you use this code or analysis, please cite:

```bibtex
@unpublished{dedollarization_sanctions_2025,
  title   = {Sanctions, Infrastructure, and De-Dollarization: Panel Evidence
             on the Push–Pull–Resist Framework (2010–2023)},
  author  = {[Author(s)]},
  year    = {2025},
  note    = {Working paper}
}
```


## Keywords

`de-dollarization` · `cross-border payment infrastructure` · `CIPS` · `financial sanctions` · `BRICS+` · `renminbi internationalization` · `push–pull model` · `Sanctions Paradox` · `panel econometrics` · `Callaway–Sant'Anna` · `PPML` · `event study` · `two-way fixed effects`

