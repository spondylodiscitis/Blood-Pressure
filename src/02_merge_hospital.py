from pathlib import Path
import yaml
import pandas as pd

from preprocess_hospital import load_hospital_domain

DOMAINS = ["cohort", "inform", "dia", "sur", "drug", "vs"]


if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out_dir = Path(cfg["paths"]["output_dir"]) / "intermediate"
    out_dir.mkdir(parents=True, exist_ok=True)

    for cohort, directory in [
        ("ca", cfg["paths"]["ca_dir"]),
        ("nca", cfg["paths"]["nca_dir"]),
    ]:
        for domain in DOMAINS:
            try:
                df = load_hospital_domain(directory, cohort, domain)
            except FileNotFoundError:
                print(f"[SKIP] {cohort}_{domain}: no shards")
                continue

            out_path = out_dir / f"{cohort}_{domain}.parquet"
            try:
                df.to_parquet(out_path, index=False)
                print(f"[SAVE] {out_path}")
            except Exception:
                csv_path = out_dir / f"{cohort}_{domain}.csv"
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                print(f"[SAVE] {csv_path} (parquet unavailable)")
