"""
Template for creating 7-day Day/Night windows.

This file intentionally keeps the windowing logic simple.
Clinical inclusion/exclusion rules should be finalized before publication.
"""
from pathlib import Path
import yaml
import numpy as np
import pandas as pd


def add_day_night(df, timestamp_col="_timestamp", day_start=6, night_start=18):
    out = df.copy()
    hour = pd.to_datetime(out[timestamp_col], errors="coerce").dt.hour
    out["period"] = np.where(
        (hour >= day_start) & (hour < night_start),
        "day",
        "night",
    )
    return out


def aggregate_day_night(df):
    agg = (
        df.groupby(["연구번호", "_date", "period"], as_index=False)
        .agg(
            SBP_mean=("SBP", "mean"),
            SBP_std=("SBP", "std"),
            SBP_min=("SBP", "min"),
            SBP_max=("SBP", "max"),
            DBP_mean=("DBP", "mean"),
            DBP_std=("DBP", "std"),
            DBP_min=("DBP", "min"),
            DBP_max=("DBP", "max"),
            measurement_count=("SBP", "count"),
        )
    )
    return agg


if __name__ == "__main__":
    print(
        "Template only: connect this script to the cleaned/censored VS table "
        "after surgery and medication rules are finalized."
    )
