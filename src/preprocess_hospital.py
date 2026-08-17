"""
Hospital EHR preprocessing example.

Important design rule:
Physical CSV shards are NOT independent datasets.
All matching shards are concatenated before patient-level processing.
"""

from __future__ import annotations

from pathlib import Path
import re
import pandas as pd


def shard_number(path: Path) -> int:
    """Extract trailing shard number from xxx_12.csv."""
    m = re.search(r"_(\d+)\.csv$", path.name)
    return int(m.group(1)) if m else 10**12


def discover_shards(data_dir: str | Path, pattern: str) -> list[Path]:
    files = list(Path(data_dir).glob(pattern))
    return sorted(files, key=lambda p: (shard_number(p), p.name))


def read_csv_robust(path: Path) -> pd.DataFrame:
    """Try common encodings used by exported hospital CSV files."""
    encodings = ["utf-8-sig", "utf-8", "cp949", "euc-kr", "utf-16", "latin1"]
    last_error = None

    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False)
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"Could not read {path}: {last_error}")


def load_sharded_csv(
    data_dir: str | Path,
    pattern: str,
    patient_col: str = "연구번호",
    add_source: bool = True,
) -> pd.DataFrame:
    """
    Load every shard matching pattern.

    Example:
        load_sharded_csv("/data/ca", "ca_drug_*.csv")

    The same patient may appear in several shards.
    """
    files = discover_shards(data_dir, pattern)

    if not files:
        raise FileNotFoundError(f"No files found: {Path(data_dir) / pattern}")

    frames = []

    for path in files:
        df = read_csv_robust(path)

        if add_source:
            df["_source_file"] = path.name
            df["_source_shard"] = shard_number(path)

        frames.append(df)

    merged = pd.concat(frames, ignore_index=True, sort=False)

    print(f"[LOAD] pattern={pattern}")
    print(f"[LOAD] shards={len(files)}")
    print(f"[LOAD] rows={len(merged):,}")

    if patient_col in merged.columns:
        print(f"[LOAD] unique patients={merged[patient_col].nunique(dropna=True):,}")

        shard_count = (
            merged.dropna(subset=[patient_col])
            .groupby(patient_col)["_source_file"]
            .nunique()
        )
        spanning = int((shard_count > 1).sum())
        print(f"[LOAD] patients spanning >1 shard={spanning:,}")

    return merged


def normalize_yyyymmdd(series: pd.Series) -> pd.Series:
    text = (
        series.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )
    return pd.to_datetime(text, format="%Y%m%d", errors="coerce")


def normalize_hhmmss(series: pd.Series) -> pd.Series:
    text = (
        series.astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(6)
    )
    return text


def build_bp_timestamp(
    df: pd.DataFrame,
    date_col: str = "기록일자",
    time_col: str = "기록시간",
) -> pd.Series:
    date = normalize_yyyymmdd(df[date_col])

    if time_col not in df.columns:
        return date

    hhmmss = normalize_hhmmss(df[time_col])

    ts = pd.to_datetime(
        date.dt.strftime("%Y-%m-%d") + " " +
        hhmmss.str.slice(0, 2) + ":" +
        hhmmss.str.slice(2, 4) + ":" +
        hhmmss.str.slice(4, 6),
        errors="coerce",
    )
    return ts


def deduplicate_and_sort(
    df: pd.DataFrame,
    patient_col: str,
    sort_cols: list[str],
) -> pd.DataFrame:
    before = len(df)

    # _source columns should not make otherwise-identical clinical rows unique.
    source_cols = [c for c in ["_source_file", "_source_shard"] if c in df.columns]
    clinical_cols = [c for c in df.columns if c not in source_cols]

    dup_mask = df.duplicated(subset=clinical_cols, keep="first")
    print(f"[QC] exact clinical duplicates={dup_mask.sum():,}")

    out = df.loc[~dup_mask].copy()

    valid_sort_cols = [c for c in [patient_col, *sort_cols] if c in out.columns]
    out = out.sort_values(valid_sort_cols, kind="stable").reset_index(drop=True)

    print(f"[QC] rows: {before:,} -> {len(out):,}")
    return out


def load_hospital_domain(
    base_dir: str | Path,
    cohort: str,
    domain: str,
) -> pd.DataFrame:
    """
    cohort: 'ca' or 'nca'
    domain: 'cohort', 'inform', 'dia', 'sur', 'drug', 'vs'
    """
    pattern = f"{cohort}_{domain}_*.csv"
    df = load_sharded_csv(base_dir, pattern)

    if domain == "vs":
        df["_timestamp"] = build_bp_timestamp(df)
        sort_cols = ["_timestamp"]

    elif domain == "drug":
        if "실시일자" in df.columns:
            df["_event_date"] = normalize_yyyymmdd(df["실시일자"])
        elif "처방일자" in df.columns:
            df["_event_date"] = normalize_yyyymmdd(df["처방일자"])
        sort_cols = ["_event_date"]

    elif domain == "sur":
        if "수술일자" in df.columns:
            df["_event_date"] = normalize_yyyymmdd(df["수술일자"])
        sort_cols = ["_event_date"]

    elif domain == "dia":
        if "진단일자" in df.columns:
            df["_event_date"] = normalize_yyyymmdd(df["진단일자"])
        sort_cols = ["_event_date"]

    else:
        sort_cols = []

    return deduplicate_and_sort(
        df,
        patient_col="연구번호",
        sort_cols=sort_cols,
    )


def prepare_vital_signs(vs: pd.DataFrame) -> pd.DataFrame:
    out = vs.copy()

    sbp_col = "BP(S)_클린징" if "BP(S)_클린징" in out.columns else "BP(S)"
    dbp_col = "BP(D)_클린징" if "BP(D)_클린징" in out.columns else "BP(D)"

    out["SBP"] = pd.to_numeric(out[sbp_col], errors="coerce")
    out["DBP"] = pd.to_numeric(out[dbp_col], errors="coerce")

    # Do not automatically replace missing BP with zero.
    out.loc[out["SBP"] <= 0, "SBP"] = pd.NA
    out.loc[out["DBP"] <= 0, "DBP"] = pd.NA

    return out


if __name__ == "__main__":
    # Example paths only.
    CA_DIR = "/home/ads_lj/visiontask/혈압/data/ca"
    NCA_DIR = "/home/ads_lj/visiontask/혈압/data/nca"

    # This automatically loads ca_drug_1 ... ca_drug_N.
    ca_drug = load_hospital_domain(CA_DIR, "ca", "drug")
    ca_vs = prepare_vital_signs(load_hospital_domain(CA_DIR, "ca", "vs"))

    nca_drug = load_hospital_domain(NCA_DIR, "nca", "drug")
    nca_vs = prepare_vital_signs(load_hospital_domain(NCA_DIR, "nca", "vs"))

    print(ca_drug.shape, ca_vs.shape)
    print(nca_drug.shape, nca_vs.shape)
