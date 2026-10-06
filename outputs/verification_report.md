# Verification report

| Status | Section | Quantity | Paper | Regenerated |
|---|---|---|---|---|
| PASS | 5.1-5.2 CIPS | TWFE CIPS -> clearing bank, baseline | 0.3778 | 0.3778 |
| PASS | 5.1-5.2 CIPS | TWFE + group trend | 0.1784 | 0.1784 |
| PASS | 5.1-5.2 CIPS | Differential trend per year | 0.0307 | 0.0307 |
| PASS | 5.1-5.2 CIPS | Swap line, group trend | 0.0006 | 0.0006 |
| PASS | 5.1-5.2 CIPS | Event-study pre-trend slope | 0.0987 | 0.0987 |
| PASS | 5.1-5.2 CIPS | Event-study level shift at t=0 | 0.0898 | 0.0898 |
| PASS | 5.1-5.2 CIPS | CS-DiD simple ATT (paper aggregation) | 0.0518 | 0.0518 |
| PASS | 5.1-5.2 CIPS | CS-DiD SE, cells treated as independent (bootstrap-cell, seed-dependent) | 0.0173 | 0.0173 |
| PASS | 5.1-5.2 CIPS | Placebo t-3, clearing bank | 0.2634 | 0.2634 |
| PASS | 5.1-5.2 CIPS | Placebo t-3, invoicing | 0.0212 | 0.0212 |
| PASS | 5.1-5.2 CIPS | Clearing bank before CIPS (of 23) | 19 | 19.0000 |
| PASS | 5.3 Interaction | alpha_2 Spec (A) | -1.5655 | -1.5655 |
| PASS | 5.3 Interaction | alpha_3 Spec (A) | 1.7702 | 1.7702 |
| PASS | 5.3 Interaction | p(alpha_3) | 0.0063 | 0.0063 |
| PASS | 5.3 Interaction | alpha_3 arcsinh | 1.2214 | 1.2214 |
| PASS | 5.3 Interaction | alpha_3 CIPS | 1.5559 | 1.5559 |
| PASS | 5.3 Interaction | alpha_3 clearing bank | 2.1973 | 2.1973 |
| PASS | 5.3 Interaction | Infra* = |a2|/a3 | 0.885 | 0.8844 |
| PASS | 5.5 / App. C | Winsorize 95th | 1.0775 | 1.0775 |
| PASS | 5.5 / App. C | Winsorize 99th | 1.6409 | 1.6409 |
| PASS | 5.5 / App. C | Extensive margin | 0.7528 | 0.7528 |
| PASS | 5.5 / App. C | log(1+y) | 0.9398 | 0.9398 |
| PASS | 5.5 / App. C | Two-way clustered SE | 0.6009 | 0.6009 |
| PASS | 5.5 / App. C | Drop RUS + CHN | 2.786 | 2.7860 |
| PASS | 5.5 / App. C | FE only | 6.7926 | 6.7926 |
| PASS | 5.5 / App. C | Drop 2015 cohort | 2.823 | 2.8230 |
| PASS | 5.5 / App. C | PPML sanctions main effect | 14.9513 | 14.9513 |
| PASS | 5.5 / App. C | IV first-stage F | 1.8 | 1.7984 |
| PASS | 2.3 Quadrants | Quadrant Q1 mean | 0.036 | 0.0362 |
| PASS | 2.3 Quadrants | Quadrant Q2 mean | 0.246 | 0.2459 |
| PASS | 5.4 / 6 Temporal | alpha_3 2010-2021 | 1.5758 | 1.5758 |
| PASS | 5.4 / 6 Temporal | alpha_3 2015-2021 | 3.005 | 3.0051 |
| PASS | 5.4 / 6 Temporal | alpha_3 2022-2023 | 20.8046 | 20.8046 |
| PASS | 5.4 / 6 Temporal | N 2022-2023 | 188 | 188.0000 |
| PASS | 5.4 / 6 Temporal | Post-2022 excl. Argentina | -1.7463 | -1.7463 |
| PASS | 5.4 / 6 Temporal | DFBETA Argentina | 2.6227 | 2.6227 |
| PASS | 5.4 / 6 Temporal | Bootstrap CI low (seed-dependent) | -7.98 | -7.4856 |
| PASS | 5.4 / 6 Temporal | Bootstrap CI high (seed-dependent) | 47.21 | 50.6429 |
| PASS | 7.6 Penalized SCM | Indonesia distance to Russia | 0.629 | 0.6292 |
| PASS | 7.6 Penalized SCM | Countries in ranking | 154 | 154.0000 |
| PASS | 7.6 Penalized SCM | CV lambda, BMP | 1.0 | 1.0000 |
| PASS | 7.6 Penalized SCM | CV lambda, settlement | 0.0 | 0.0000 |
| PASS | 7.3 SCM | BMP gap lambda=0 | 1.5854 | 1.5854 |
| PASS | 7.3 SCM | BMP pre-RMSE lambda=0 | 0.2712 | 0.2712 |
| PASS | 7.3 SCM | BMP gap lambda=1 | 1.9465 | 1.9465 |
| PASS | 7.3 SCM | BMP gap lambda=100 | 3.0887 | 3.0886 |
| PASS | 7.3 SCM | Settlement gap lambda=0 | -0.609 | -0.6090 |
| PASS | 7.3 SCM | Settlement pre-RMSE | 0.0692 | 0.0692 |
| PASS | 7.3 SCM | BMP placebo p (157 donors) | 0.0255 | 0.0255 |
| PASS | 7.3 SCM | Settlement placebo p | 0.0701 | 0.0701 |
| PASS | 7.3 SCM | BMP penalized placebo p | 0.0211 | 0.0211 |
| PASS | 7.3 SCM | BMP donors constant pre-2022 | 140 | 140.0000 |
| PASS | 7.4 Russia | Russia RMB invoicing 2023 | 29.353 | 29.3526 |
| PASS | 7.4 Russia | Russia China share 2023 (rebuilt) | 28.4 | 28.3893 |

## Re-estimated / since-submission results (no paper target)

| Quantity | Value |
|---|---|
| CS-DiD ATT, bootstrap aggregation, no anticipation | 0.0518 |
|   ... bootstrap SE (paper reported 0.018) | 0.0453 |
| CS-DiD ATT, 2-year anticipation | 0.3869 |
|   ... bootstrap SE | 0.0800 |
| CIPS joiners with a clearing bank | 23 |
| Delta-method SE of Infra* | 0.2204 |
| SD of sanctions among sanctioned obs (paper uses 0.11) | 0.1054 |
| SD of sanctions in estimation sample | 0.0612 |
| LOO (Spec A): alpha_3 > 0 count | 112 |
| LOO (Spec A): p < 0.05 count | 111 |
| LOO (Spec A): refits | 112 |
| LOO (Spec A): excl. Russia alpha_3 | 2.7860 |
| LOO (Spec A): excl. Russia p | 0.0950 |
| LOO (99th): alpha_3 > 0 count | 112 |
| LOO (99th): p < 0.05 count | 111 |
| Post-2022 obs with invoicing data | 242 |
| Post-2022 obs in regression | 188 |
| alpha_3, Russia 2022-23 restored | 7.2949 |
| Infra*, Russia 2022-23 restored | 0.4474 |
| Post-2022 permutation p | 0.0000 |
| Post-2022 alpha_3, Russia restored | 18.4540 |
|   ... excluding Argentina | 16.4158 |
|   ... p | 0.0000 |
| BRICS full members in top-10 peers | 4 |
| Hypergeometric p (members only) | 0.0003 |
| BMP placebo p, informative donors only | 0.2353 |
| Settlement proxy vs China share x SWIFT share (corr) | 1.0000 |
| Proxy zeros where China share is missing | 1.0000 |
| Russia China-share pre-trend (pp/yr) | 0.7893 |
| alpha_3 high China exposure (99th) | 1.9280 |
| alpha_3 low China exposure (99th) | 0.7936 |
