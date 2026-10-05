#!/usr/bin/env python
"""Regenerate every MEG 2026 slide figure and verify every number against the paper.

Examples
  python run_all.py --panel MASTER_PANEL.csv
  python run_all.py --panel MASTER_PANEL.csv \
      --panel-full data/MASTER_PANEL_v25b_clean.csv \
      --rebuilt data/MASTER_PANEL_v25c_rebuilt.csv \
      --tracker data/swift_rmb_tracker_manual_long.csv
  python run_all.py --only s02 s06          # run selected steps
  python run_all.py --fast                  # fewer bootstrap draws, skip slow placebo
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from meg.common import Opts

STEPS = ["s01", "s02", "s03", "s04", "s05", "s06"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--panel", default="MASTER_PANEL.csv",
                    help="repository panel (MASTER_PANEL.csv)")
    ap.add_argument("--panel-full", default=None,
                    help="MASTER_PANEL_v25b_clean.csv (adds BMP for the SCM step)")
    ap.add_argument("--rebuilt", default=None,
                    help="MASTER_PANEL_v25c_rebuilt.csv (rebuilt China-trade share)")
    ap.add_argument("--tracker", default=None, help="swift_rmb_tracker_manual_long.csv")
    ap.add_argument("--out", default="output", help="output folder")
    ap.add_argument("--only", nargs="*", choices=STEPS, help="run only these steps")
    ap.add_argument("--fast", action="store_true", help="quick run (fewer draws)")
    ap.add_argument("--fresh", action="store_true", help="delete previous results.json first")
    a = ap.parse_args(argv)

    Opts.panel = Path(a.panel)
    Opts.panel_full = Path(a.panel_full) if a.panel_full else None
    Opts.rebuilt = Path(a.rebuilt) if a.rebuilt else None
    Opts.tracker = Path(a.tracker) if a.tracker else None
    Opts.out = Path(a.out)
    Opts.fast = a.fast
    Opts.out.mkdir(parents=True, exist_ok=True)
    if a.fresh and (Opts.out / "results.json").exists():
        (Opts.out / "results.json").unlink()

    for p, flag in [(Opts.panel, "--panel"), (Opts.panel_full, "--panel-full"),
                    (Opts.rebuilt, "--rebuilt"), (Opts.tracker, "--tracker")]:
        if p is not None and not p.exists():
            sys.exit(f"File given to {flag} not found: {p}")

    from meg import s01_part1, s02_part2, s03_temporal, s04_scm, s05_russia, s06_verify
    mods = dict(zip(STEPS, [s01_part1, s02_part2, s03_temporal, s04_scm, s05_russia, s06_verify]))
    t0 = time.time()
    for s in (a.only or STEPS):
        t = time.time()
        mods[s].run()
        print(f"  [{s} done in {time.time() - t:.0f}s]")
    print(f"\nAll done in {(time.time() - t0) / 60:.1f} min. Figures: {Opts.out / 'figures'}  "
          f"Tables: {Opts.out / 'tables'}  Report: {Opts.out / 'verification_report.md'}")


if __name__ == "__main__":
    main()
