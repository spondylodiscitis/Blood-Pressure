from pathlib import Path
import json
import yaml
import numpy as np
import pandas as pd

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    balanced_accuracy_score,
    accuracy_score,
    f1_score,
    confusion_matrix,
)
from sklearn.model_selection import LeaveOneOut
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    path = Path(cfg["paths"]["output_dir"]) / "mouse_features.csv"
    df = pd.read_csv(path)

    meta = {"animal_id", "group", "label"}
    features = [
        c for c in df.columns
        if c not in meta and pd.api.types.is_numeric_dtype(df[c])
    ]

    X = df[features]
    y = df["label"].astype(int).to_numpy()

    loo = LeaveOneOut()
    probs = np.zeros(len(df), dtype=float)

    for train_idx, test_idx in loo.split(X):
        if len(np.unique(y[train_idx])) < 2:
            probs[test_idx] = y[train_idx].mean()
            continue

        model = Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=cfg["split"]["random_seed"],
            )),
        ])

        model.fit(X.iloc[train_idx], y[train_idx])
        probs[test_idx] = model.predict_proba(X.iloc[test_idx])[:, 1]

    pred = (probs >= cfg["evaluation"]["threshold"]).astype(int)
    cm = confusion_matrix(y, pred, labels=[0, 1])

    result = df[["animal_id", "group", "label"]].copy()
    result["predicted_probability"] = probs
    result["predicted_label"] = pred

    result.to_csv(
        Path(cfg["paths"]["output_dir"]) / "mouse_predictions.csv",
        index=False,
        encoding="utf-8-sig",
    )

    metrics = {
        "auroc": float(roc_auc_score(y, probs)) if len(np.unique(y)) == 2 else None,
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "accuracy": float(accuracy_score(y, pred)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "confusion_matrix": cm.tolist(),
        "evaluation": "leave-one-animal-out",
        "n_animals": int(len(df)),
        "features": features,
    }

    Path(cfg["paths"]["output_dir"], "mouse_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(result.to_string(index=False))
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
