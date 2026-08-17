from pathlib import Path
import yaml
import pandas as pd


def read_intermediate(path_base: Path):
    pq = path_base.with_suffix(".parquet")
    csv = path_base.with_suffix(".csv")

    if pq.exists():
        return pd.read_parquet(pq)
    if csv.exists():
        return pd.read_csv(csv, low_memory=False)

    raise FileNotFoundError(path_base)


def summarize_vs(df, cohort):
    sbp_col = "BP(S)_클린징" if "BP(S)_클린징" in df.columns else "BP(S)"
    dbp_col = "BP(D)_클린징" if "BP(D)_클린징" in df.columns else "BP(D)"

    sbp = pd.to_numeric(df[sbp_col], errors="coerce")
    dbp = pd.to_numeric(df[dbp_col], errors="coerce")

    by_patient = df.groupby("연구번호").size()

    return {
        "cohort": cohort,
        "rows": len(df),
        "patients": df["연구번호"].nunique(),
        "sbp_available_pct": sbp.notna().mean() * 100,
        "dbp_available_pct": dbp.notna().mean() * 100,
        "median_measurements_per_patient": by_patient.median(),
        "mean_measurements_per_patient": by_patient.mean(),
    }


if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    inter = Path(cfg["paths"]["output_dir"]) / "intermediate"
    rows = []

    for cohort in ["ca", "nca"]:
        try:
            vs = read_intermediate(inter / f"{cohort}_vs")
            rows.append(summarize_vs(vs, cohort))
        except FileNotFoundError:
            print(f"[WARN] missing {cohort}_vs intermediate")

    summary = pd.DataFrame(rows)
    print(summary.to_string(index=False))

    out = Path(cfg["paths"]["output_dir"]) / "human_qc_summary.csv"
    summary.to_csv(out, index=False, encoding="utf-8-sig")
