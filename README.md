# MEG 2026 — figure regeneration and result verification

This package regenerates every figure in `MEG2026_slides_content_v2.md` and checks every number against the submitted paper. It starts from the public repository's `MASTER_PANEL.csv` and uses the same variable construction as `sanctions_dedollarization_panel.ipynb`, `dedollar_v24_comprehensive.ipynb` (CS-DiD), `dedollar_v29_final.ipynb` (Appendix C) and `09_scm_penalized_v2(_finalize).ipynb` (SCM).

## 1. Setup (one time)

```bash
cd meg_replication
python3.12 -m venv .venv             # 3.11 / 3.12 recommended; check with: python3.12 --version
source .venv/bin/activate            # Windows: .venv\Scripts\activate
bash install.sh                      # or: bash install.sh mirror   (slow / blocked PyPI)
```

`install.sh` runs `pip install -r requirements.txt`, then `pip install --no-deps csdid==0.4.2 drdid==1.1.6`, then an import check. csdid is installed without its declared dependencies on purpose: it lists plotnine and twine but never imports them.

## 2. Inputs

| Flag | File | Needed for | Where it comes from |
|---|---|---|---|
| `--panel` | `MASTER_PANEL.csv` | everything | GitHub repo root (note the upper-case name) |
| `--panel-full` | `MASTER_PANEL_v25b_clean.csv` | SCM with BMP (Slides 9–10) | your local data folder (the repo copy has no BMP columns) |
| `--rebuilt` | `MASTER_PANEL_v25c_rebuilt.csv` | Slide 11 trade panel, Appendix A2 heterogeneity | `pathc/data/` (written by `run_10_apply_rebuilt.py`) |
| `--tracker` | `swift_rmb_tracker_manual_long.csv` | Slide 11 tracker ranks | your local data folder |

Only `--panel` is required. Any step whose optional input is missing is skipped, and the report marks it SKIP.

## 3. Run

```bash
# full run (about 25–40 min; the SCM placebo loops take most of the time)
python run_all.py --fresh \
  --panel MASTER_PANEL.csv \
  --panel-full data/MASTER_PANEL_v25b_clean.csv \
  --rebuilt   data/MASTER_PANEL_v25c_rebuilt.csv \
  --tracker   data/swift_rmb_tracker_manual_long.csv

# quick check (about 5 min: fewer bootstrap draws, skips the penalized placebo)
python run_all.py --fresh --fast --panel MASTER_PANEL.csv --panel-full data/MASTER_PANEL_v25b_clean.csv

# single steps
python run_all.py --only s02 s06 --panel MASTER_PANEL.csv
```

Outputs are written to `output/figures/` (PNG at 300 dpi plus PDF), `output/tables/` (CSV), `output/results.json` and `output/verification_report.md` (PASS / FAIL / NEW / SKIP for every number).

## 4. Steps → slides

| Step | Script | Slide | Figures |
|---|---|---|---|
| s01 | `meg/s01_part1.py` | 5, A1 | `fig_s5_event_study`, `fig_a1_csdid_dynamic` |
| s02 | `meg/s02_part2.py` | 6, 7, A2 | `fig_s6_marginal_effects`, `fig_s7_loo_caterpillar` |
| s03 | `meg/s03_temporal.py` | 8 | `fig_s8_argentina_loo` |
| s04 | `meg/s04_scm.py` | 9, 10, A3 | `fig_s9_lambda_sweep`, `fig_s9_donor_weights`, `fig_s10_scm`, `fig_s10_scm_3panel_archival` |
| s05 | `meg/s05_russia.py` | 11, A2 | `fig_s11_russia_facts` |
| s06 | `meg/s06_verify.py` | all | `verification_report.md` |

## 5. What is re-estimated, and why

- **CS-DiD standard error.** The paper's SE of 0.018 combined the ATT(g,t) cells as if they were independent. `csdid.aggte(..., bstrap=True)` uses the influence function instead; it is reported side by side with the paper's version in `a1_csdid_sensitivity.csv`.
- **Anticipation.** CS-DiD is re-run with `anticipation = 1, 2` and with a not-yet-treated control group. The rollout-timing table shows clearing banks preceding CIPS accession.
- **Russia 2022–23.** These two observations drop out of every controlled regression because financial depth is missing. `restore_russia()` fills them with the 2021 value (the LOCF rule the paper already uses for Chinn–Ito). Every affected table reports the published sample alongside the restored one.
- **Leave-one-out.** The loop runs over countries in the estimation sample (112), not over all countries with invoicing data (121). Dropping a country that is not in the sample does not change the estimate, so counting it would inflate the tally.
- **SCM placebo.** The p-value is reported both as the paper's n/N and as (n+1)/(N+1), and both for all donors and for informative donors only (those with a non-constant pre-period outcome).
- **Post-2022 bootstrap and permutation.** These use an exact dummy-variable OLS. The code checks that its point estimate equals PanelOLS on the actual sample, and skips draws in which α₃ is not identified, as the paper's code did. Percentiles differ slightly from the paper's because the random-number streams differ.
- **SLSQP convergence.** The SCM weights use the paper's SLSQP settings so that the paper's numbers reproduce exactly. SLSQP reports "not converged" at λ ≥ 1 because the tolerance is very tight. The convex-QP check in `pathc/scmlib` (cvxpy, multi-start) gave the same weights.

## 6. Values to confirm before presenting

- BRICS status lists (`BRICS_MEMBERS / INVITED / PARTNERS` in `s04_scm.py`) are set as of 2025. Check them against an official source on the day of the talk.
- Russia's RMB clearing-bank designation year (the panel codes 2015).

## 7. Figure style

All figures use one y-axis per panel. Wherever the originals used a dual axis (marginal-effects density, λ sweep, Argentina), the second measure is now a separate panel. Categorical colours are the first three validated slots (blue / orange / aqua). Russia's highlight colour is always paired with a text label.
