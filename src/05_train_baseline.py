"""
Simple human baseline example.
Expected input: one row per patient/window and a `label` column.
"""
from pathlib import Path
import json
import yaml
import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    balanced_accuracy_score,
    accuracy_score,
    f1_score,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupShuffleSplit


def specificity_from_cm(cm):
    if cm.shape != (2, 2):
        return np.nan
    tn, fp, fn, tp = cm.ravel()
    return tn / (tn + fp) if (tn + fp) else np.nan


if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    feature_path = Path(cfg["paths"]["output_dir"]) / "human_feature_table.csv"
    if not feature_path.exists():
        raise FileNotFoundError(
            f"{feature_path} not found. Build the final human feature table first."
        )

    df = pd.read_csv(feature_path)

    required = {"연구번호", "label"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    ignore = {"연구번호", "label", "window_id", "split"}
    feature_cols = [
        c for c in df.columns
        if c not in ignore and pd.api.types.is_numeric_dtype(df[c])
    ]

    X = df[feature_cols]
    y = df["label"].astype(int)
    groups = df["연구번호"].astype(str)

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=cfg["split"]["test_fraction"],
        random_state=cfg["split"]["random_seed"],
    )
    train_idx, test_idx = next(splitter.split(X, y, groups=groups))

    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            random_state=cfg["split"]["random_seed"],
        )),
    ])

    pipe.fit(X.iloc[train_idx], y.iloc[train_idx])

    prob = pipe.predict_proba(X.iloc[test_idx])[:, 1]
    pred = (prob >= cfg["evaluation"]["threshold"]).astype(int)
    yt = y.iloc[test_idx].to_numpy()

    cm = confusion_matrix(yt, pred, labels=[0, 1])

    metrics = {
        "auroc": float(roc_auc_score(yt, prob)),
        "balanced_accuracy": float(balanced_accuracy_score(yt, pred)),
        "accuracy": float(accuracy_score(yt, pred)),
        "f1": float(f1_score(yt, pred, zero_division=0)),
        "specificity": float(specificity_from_cm(cm)),
        "confusion_matrix": cm.tolist(),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "features": feature_cols,
    }

    print(json.dumps(metrics, indent=2, ensure_ascii=False))

    out = Path(cfg["paths"]["output_dir"]) / "human_baseline_metrics.json"
    out.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
