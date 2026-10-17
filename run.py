#!/usr/bin/env python
"""Single entry point: download -> SQL star schema -> KPIs -> charts -> reports.

Usage:
    python run.py            # full pipeline (re-uses raw files if present)
    python run.py --refresh  # force a fresh download from the KAPSARC API
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from pos_dashboard.download import download_all  # noqa: E402
from pos_dashboard.kpis import run_kpis  # noqa: E402
from pos_dashboard.report import build_reports  # noqa: E402
from pos_dashboard.transform import build_star_schema  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="re-download raw data")
    args = ap.parse_args()
    t0 = time.time()
    download_all(force=args.refresh)
    con = build_star_schema()
    frames, kpis = run_kpis(con)
    con.close()
    build_reports(frames, kpis)
    print(f"[done] pipeline finished in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
