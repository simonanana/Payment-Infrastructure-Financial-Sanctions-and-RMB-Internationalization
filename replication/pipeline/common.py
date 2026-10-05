"""Shared data construction, estimators, plotting style and result registry.

Variable construction reproduces the repository notebook
(`sanctions_dedollarization_panel.ipynb`, cell "Load Panel & Construct
Variables") exactly, so every number in the submitted paper is regenerated
from the same definitions before any re-estimation is layered on top.
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------
# Constants (identical to the paper notebooks)
# --------------------------------------------------------------------------
SANC = "sanction_fin_norm_fixed"
CONTROLS = ["ln_gdp", "ln_trade_openness", "financial_depth_it",
            "capital_openness_it_filled", "gdp_growth_it", "inflation_it_w",
            "fdi_inflow_gdp_it_w", "unga_align_norm_it"]
CS = " + ".join(CONTROLS)
WINSOR_Q = 0.995          # paper Spec (A); data section text says 99th -> see s02 ladder
SENDERS = ["USA", "GBR", "FRA", "DEU", "CAN", "AUS", "JPN"]
TARGETS = ["RUS", "IRN", "PRK", "SYR", "CUB", "VEN", "MMR", "BLR"]
INTER_RHS = f"rmb_infra_it + {SANC} + infra_x_sanction + {CS}"
FE = " + EntityEffects + TimeEffects"

# --------------------------------------------------------------------------
# Paths / run options (set once by run_all.py)
# --------------------------------------------------------------------------
class Opts:
    panel: Path = Path("MASTER_PANEL.csv")
    panel_full: Path | None = None        # MASTER_PANEL_v25b_clean.csv (BMP, SCM inputs)
    rebuilt: Path | None = None           # MASTER_PANEL_v25c_rebuilt.csv (rebuilt China trade)
    tracker: Path | None = None           # swift_rmb_tracker_manual_long.csv
    out: Path = Path("output")
    fast: bool = False
    seed: int = 42

    @classmethod
    def figdir(cls) -> Path:
        p = cls.out / "figures"; p.mkdir(parents=True, exist_ok=True); return p

    @classmethod
    def tabdir(cls) -> Path:
        p = cls.out / "tables"; p.mkdir(parents=True, exist_ok=True); return p


# --------------------------------------------------------------------------
# Result registry -> output/results.json (read by s06_verify)
# --------------------------------------------------------------------------
def _results_path() -> Path:
    Opts.out.mkdir(parents=True, exist_ok=True)
    return Opts.out / "results.json"


def record(key: str, value) -> None:
    path = _results_path()
    data = json.loads(path.read_text()) if path.exists() else {}
    if isinstance(value, (np.floating, np.integer)):
        value = value.item()
    data[key] = value
    path.write_text(json.dumps(data, indent=2, default=float))


def load_results() -> dict:
    path = _results_path()
    return json.loads(path.read_text()) if path.exists() else {}


def save_table(df: pd.DataFrame, name: str) -> Path:
    path = Opts.tabdir() / f"{name}.csv"
    df.to_csv(path, index=False)
    print(f"    table  -> {path}")
    return path


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def load_panel(path: Path | None = None) -> pd.DataFrame:
    """Load a panel and build every derived variable used in the paper."""
    path = Path(path or Opts.panel)
    if not path.exists():
        raise FileNotFoundError(
            f"Panel not found: {path}\n"
            "  The repository ships it as MASTER_PANEL.csv (upper case). "
            "Pass --panel <path>.")
    df = pd.read_csv(path, low_memory=False)
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    need = ["iso3", "year", "CIPSit", "clearing_bank_it", "swap_line_it",
            "rmb_infra_it", "rmb_invoicing_share", SANC] + CONTROLS
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise KeyError(f"{path.name} lacks required columns: {missing}")

    first = df.loc[df["CIPSit"] == 1].groupby("iso3")["year"].min()
    df["g_first_treat"] = df["iso3"].map(first)
    df["treated_direct"] = df["g_first_treat"].notna().astype(int)
    df["trend_direct"] = df["treated_direct"] * (df["year"] - df["year"].min())

    df["infra_x_sanction"] = df["rmb_infra_it"].fillna(0) * df[SANC].fillna(0)
    df["cips_x_sanction"] = df["CIPSit"].fillna(0) * df[SANC].fillna(0)
    df["clear_x_sanction"] = df["clearing_bank_it"].fillna(0) * df[SANC].fillna(0)

    y = pd.to_numeric(df["rmb_invoicing_share"], errors="coerce")
    y[y < 0] = np.nan
    df["rmb_invoicing_share"] = y
    df["rmb_invoicing_w"] = y.clip(upper=y.quantile(WINSOR_Q))
    df["rmb_inv_asinh"] = np.arcsinh(y)

    df["role"] = "Observer"
    df.loc[df["iso3"].isin(SENDERS), "role"] = "Sender"
    df.loc[df["iso3"].isin(TARGETS), "role"] = "Target"
    return df


def restore_russia(df: pd.DataFrame) -> pd.DataFrame:
    """Fill Russia's missing 2022-23 financial depth with its 2021 value (LOCF).

    In the published sample these two observations are silently dropped by
    listwise deletion; they carry the two largest invoicing values in the panel.
    LOCF is the rule the paper already applies to the Chinn-Ito index.
    """
    d = df.copy()
    m21 = d.loc[(d.iso3 == "RUS") & (d.year == 2021), "financial_depth_it"]
    mask = (d.iso3 == "RUS") & (d.year >= 2022) & d["financial_depth_it"].isna()
    if len(m21) and mask.any():
        d.loc[mask, "financial_depth_it"] = float(m21.iloc[0])
    return d


# --------------------------------------------------------------------------
# Estimators
# --------------------------------------------------------------------------
def fit_twfe(data: pd.DataFrame, formula: str, cluster_time: bool = False):
    from linearmodels.panel import PanelOLS
    dp = data.set_index(["iso3", "year"]).sort_index()
    mod = PanelOLS.from_formula(formula, dp, drop_absorbed=True)
    if cluster_time:
        return mod.fit(cov_type="clustered", cluster_entity=True, cluster_time=True)
    return mod.fit(cov_type="clustered", cluster_entity=True)


def coef(m, var: str) -> dict:
    return {"beta": float(m.params[var]), "se": float(m.std_errors[var]),
            "p": float(m.pvalues[var]), "n": int(m.nobs)}


def interaction(data: pd.DataFrame, dv: str = "rmb_invoicing_w",
                controls: str = CS, **kw):
    f = f"{dv} ~ rmb_infra_it + {SANC} + infra_x_sanction"
    f += (f" + {controls}" if controls else "") + FE
    return fit_twfe(data, f, **kw)


def stars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


# --------------------------------------------------------------------------
# Plot style (validated categorical slots 1-3 + neutral ink; see README)
# --------------------------------------------------------------------------
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#8a8984"
GRID = "#e4e3df"
BLUE = "#2a78d6"      # series 1
ORANGE = "#eb6834"    # series 2
AQUA = "#1baf7a"      # series 3
RED = "#e34948"       # highlight (Russia) - always paired with a text label


def setup_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 300,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
        "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
        "legend.fontsize": 9.5, "legend.frameon": False,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "lines.linewidth": 2.0, "figure.facecolor": "white",
    })
    return plt


def save_fig(fig, name: str):
    d = Opts.figdir()
    for ext in ("png", "pdf"):
        fig.savefig(d / f"{name}.{ext}", bbox_inches="tight")
    print(f"    figure -> {d / name}.png (+ .pdf)")
    import matplotlib.pyplot as plt
    plt.close(fig)


def banner(title: str):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)
