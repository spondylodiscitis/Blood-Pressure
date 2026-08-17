from pathlib import Path
import yaml

from preprocess_mouse import parse_mouse_workbook, make_animal_features

if __name__ == "__main__":
    with open("config/config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    out_dir = Path(cfg["paths"]["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    tidy = parse_mouse_workbook(
        xlsx_path=cfg["paths"]["mouse_xlsx"],
        mapping_path=cfg["mouse"]["mapping_path"],
        year=cfg["mouse"]["year"],
    )
    features = make_animal_features(tidy)

    tidy.to_csv(out_dir / "mouse_tidy.csv", index=False, encoding="utf-8-sig")
    features.to_csv(out_dir / "mouse_features.csv", index=False, encoding="utf-8-sig")

    print("[MOUSE] rows:", len(tidy))
    print("[MOUSE] animals:", tidy["animal_id"].nunique())
    print(features[["animal_id", "group", "label"]].to_string(index=False))
