from pathlib import Path
import re
import yaml
import pandas as pd

DOMAINS = ["cohort", "inform", "dia", "sur", "drug", "vs"]


def shard_num(path: Path):
    m = re.search(r"_(\d+)\.csv$", path.name)
    return int(m.group(1)) if m else -1


def robust_read(path: Path):
    for enc in ["utf-8-sig", "utf-8", "cp949", "euc-kr", "utf-16", "latin1"]:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception:
            pass
    raise RuntimeError(f"Cannot read {path}")


def inspect_domain(base_dir, cohort, domain):
    files = sorted(Path(base_dir).glob(f"{cohort}_{domain}_*.csv"),
                   key=lambda p: (shard_num(p), p.name))
    if not files:
        return None

    total_rows = 0
    patient_to_files = {}

    for f in files:
        df = robust_read(f)
        total_rows += len(df)

        if "연구번호" in df.columns:
            for pid in df["연구번호"].dropna().astype(str).unique():
                patient_to_files.setdefault(pid, set()).add(f.name)

    spanning = sum(len(v) > 1 for v in patient_to_files.values())

    return {
        "cohort": cohort,
        "domain": domain,
        "shards": len(files),
        "first_shard": files[0].name,
        "last_shard": files[-1].name,
        "rows": total_rows,
        "unique_patients": len(patient_to_files),
        "patients_spanning_shards": spanning,
    }


if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    rows = []
    for cohort, directory in [
        ("ca", cfg["paths"]["ca_dir"]),
        ("nca", cfg["paths"]["nca_dir"]),
    ]:
        for domain in DOMAINS:
            result = inspect_domain(directory, cohort, domain)
            if result:
                rows.append(result)

    out = pd.DataFrame(rows)
    print(out.to_string(index=False))

    out_dir = Path(cfg["paths"]["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "raw_inventory.csv", index=False, encoding="utf-8-sig")
