"""Download the raw SAMA POS CSVs from the KAPSARC public API and record a manifest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import requests

from .config import DATASETS, KAPSARC_EXPORT, KAPSARC_PAGE, RAW


def download_all(force: bool = False) -> dict:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for key, meta in DATASETS.items():
        out = RAW / f"{meta['dataset_id']}.csv"
        url = KAPSARC_EXPORT.format(dataset_id=meta["dataset_id"])
        if out.exists() and not force and key in manifest:
            print(f"[download] {out.name} already present (use --force to refresh)")
            continue
        print(f"[download] GET {url}")
        resp = requests.get(url, timeout=120, headers={"User-Agent": "pos-dashboard/1.0"})
        resp.raise_for_status()
        out.write_bytes(resp.content)
        manifest[key] = {
            **meta,
            "download_url": url,
            "landing_page": KAPSARC_PAGE.format(dataset_id=meta["dataset_id"]),
            "file": out.name,
            "bytes": len(resp.content),
            "sha256": hashlib.sha256(resp.content).hexdigest(),
            "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        print(f"[download] saved {out.name} ({len(resp.content):,} bytes)")
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    download_all()
