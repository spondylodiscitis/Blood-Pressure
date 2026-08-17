"""
Convert the mouse BP workbook into a tidy longitudinal dataset.

Expected workbook characteristics:
- one sheet per date
- repeated measurement blocks per sheet
- group name appears only on the first animal row of each group
- 3 SBP values + mean
- 3 DBP values + mean
"""

from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import numpy as np
import yaml


def normalize_group(value: str) -> str:
    x = str(value).strip()
    x = re.sub(r"^Group\s+\d+\s*", "", x, flags=re.I)
    x = re.sub(r"\s+", " ", x)
    return x.strip()


def group_for_id(group: str) -> str:
    x = normalize_group(group).lower()
    x = x.replace(".", "")
    x = re.sub(r"[^a-z0-9]+", "_", x)
    return x.strip("_")


def parse_korean_time_marker(value) -> str | None:
    """
    Examples:
        '2025-11-27 9시'  -> '09:00'
        '2025-11-27 17시' -> '17:00'
    """
    if pd.isna(value):
        return None

    text = str(value)
    m = re.search(r"(\d{1,2})\s*시", text)

    if not m:
        return None

    hour = int(m.group(1))
    return f"{hour:02d}:00"


def parse_sheet_date(sheet_name: str, year: int) -> pd.Timestamp:
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})", str(sheet_name).strip())

    if not m:
        raise ValueError(f"Unexpected sheet name: {sheet_name}")

    month, day = map(int, m.groups())
    return pd.Timestamp(year=year, month=month, day=day)


def load_mapping(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return cfg["groups"]


def parse_mouse_workbook(
    xlsx_path: str | Path,
    mapping_path: str | Path,
    year: int = 2025,
) -> pd.DataFrame:

    mapping = load_mapping(mapping_path)
    xl = pd.ExcelFile(xlsx_path)
    all_records = []

    for sheet in xl.sheet_names:
        raw = pd.read_excel(xlsx_path, sheet_name=sheet, header=None)
        sheet_date = parse_sheet_date(sheet, year)

        # Locate each repeated measurement block.
        header_rows = raw.index[
            (raw.iloc[:, 0].astype(str).str.strip() == "Group") &
            (raw.iloc[:, 1].astype(str).str.strip() == "Animal #")
        ].tolist()

        for block_idx, header_row in enumerate(header_rows):
            next_header = (
                header_rows[block_idx + 1]
                if block_idx + 1 < len(header_rows)
                else len(raw)
            )

            block = raw.iloc[header_row + 1:next_header].copy()

            # Find time marker associated with this block.
            time_value = None
            for value in block.iloc[:, 0].tolist():
                parsed = parse_korean_time_marker(value)
                if parsed:
                    time_value = parsed
                    break

            current_group = None

            for _, row in block.iterrows():
                col0 = row.iloc[0]
                animal = row.iloc[1]

                # A new group starts when col0 has a group name and col1 is numeric.
                if pd.notna(col0) and pd.notna(animal):
                    if str(animal).strip().lower() not in {"mean", "sd"}:
                        try:
                            float(animal)
                            current_group = normalize_group(col0)
                        except Exception:
                            pass

                if current_group is None:
                    continue

                # Keep animal rows only.
                try:
                    animal_no = int(float(animal))
                except Exception:
                    continue

                if current_group not in mapping:
                    # Unknown groups should never be silently labeled.
                    raise KeyError(
                        f"Group '{current_group}' not found in mapping config"
                    )

                values = [pd.to_numeric(row.iloc[i], errors="coerce") for i in range(2, 10)]

                record = {
                    "date": sheet_date.date().isoformat(),
                    "time": time_value,
                    "group": current_group,
                    "animal_no": animal_no,
                    "animal_id": f"{group_for_id(current_group)}_{animal_no}",
                    "sbp_1": values[0],
                    "sbp_2": values[1],
                    "sbp_3": values[2],
                    "sbp_mean": values[3],
                    "dbp_1": values[4],
                    "dbp_2": values[5],
                    "dbp_3": values[6],
                    "dbp_mean": values[7],
                    "label": int(mapping[current_group]["label"]),
                    "source_sheet": sheet,
                }

                all_records.append(record)

    out = pd.DataFrame(all_records)

    # Zero-only BP rows are treated as missing measurements by default.
    sbp_cols = ["sbp_1", "sbp_2", "sbp_3"]
    dbp_cols = ["dbp_1", "dbp_2", "dbp_3"]

    zero_sbp = out[sbp_cols].fillna(0).eq(0).all(axis=1)
    zero_dbp = out[dbp_cols].fillna(0).eq(0).all(axis=1)

    out.loc[zero_sbp, sbp_cols + ["sbp_mean"]] = np.nan
    out.loc[zero_dbp, dbp_cols + ["dbp_mean"]] = np.nan

    # Recalculate means from valid replicate measurements.
    out["sbp_mean"] = out[sbp_cols].mean(axis=1, skipna=True)
    out["dbp_mean"] = out[dbp_cols].mean(axis=1, skipna=True)

    out["timestamp"] = pd.to_datetime(
        out["date"].astype(str) + " " + out["time"].fillna("00:00"),
        errors="coerce",
    )

    out = out.sort_values(
        ["animal_id", "timestamp", "source_sheet"],
        kind="stable",
    ).reset_index(drop=True)

    return out


def make_animal_features(tidy: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for animal_id, g in tidy.groupby("animal_id"):
        g = g.sort_values("timestamp")
        valid = g.dropna(subset=["sbp_mean", "dbp_mean"], how="all")

        if valid.empty:
            continue

        x = (
            (valid["timestamp"] - valid["timestamp"].min())
            .dt.total_seconds()
            .div(86400)
            .to_numpy()
        )

        def slope(y):
            y = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
            mask = np.isfinite(x) & np.isfinite(y)

            if mask.sum() < 2 or np.unique(x[mask]).size < 2:
                return np.nan

            return float(np.polyfit(x[mask], y[mask], 1)[0])

        pp = valid["sbp_mean"] - valid["dbp_mean"]

        rows.append({
            "animal_id": animal_id,
            "group": valid["group"].iloc[0],
            "label": int(valid["label"].iloc[0]),
            "n_measurements": len(valid),

            "sbp_mean": valid["sbp_mean"].mean(),
            "sbp_std": valid["sbp_mean"].std(),
            "sbp_min": valid["sbp_mean"].min(),
            "sbp_max": valid["sbp_mean"].max(),
            "sbp_slope_per_day": slope(valid["sbp_mean"]),

            "dbp_mean": valid["dbp_mean"].mean(),
            "dbp_std": valid["dbp_mean"].std(),
            "dbp_min": valid["dbp_mean"].min(),
            "dbp_max": valid["dbp_mean"].max(),
            "dbp_slope_per_day": slope(valid["dbp_mean"]),

            "pulse_pressure_mean": pp.mean(),
            "pulse_pressure_std": pp.std(),
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    INPUT_XLSX = "mouse 혈압 결과.xlsx"
    MAPPING = "../config/mouse_group_mapping.yaml"

    tidy = parse_mouse_workbook(INPUT_XLSX, MAPPING, year=2025)
    features = make_animal_features(tidy)

    tidy.to_csv("mouse_tidy.csv", index=False, encoding="utf-8-sig")
    features.to_csv("mouse_features.csv", index=False, encoding="utf-8-sig")

    print("[MOUSE] tidy rows:", len(tidy))
    print("[MOUSE] animals:", tidy["animal_id"].nunique())
    print("[MOUSE] group counts:")
    print(tidy[["animal_id", "group", "label"]].drop_duplicates()["group"].value_counts())
