#!/usr/bin/env python3
"""Generate app/features_dump.json from a saved model's feature names."""
from pathlib import Path
import joblib
import json


def find_model(models_dir: Path) -> Path | None:
    if not models_dir.exists():
        return None
    pkl = sorted(models_dir.glob("*.pkl"))
    if not pkl:
        return None
    # prefer a model with 'gradient' in name
    for f in pkl:
        if 'gradient' in f.name.lower():
            return f
    return pkl[0]


def main():
    root = Path('./')
    models_dir = root / 'app' / 'services' / 'models'
    # Write features dump next to the app root so the Streamlit UI can find it at
    # `app/features_dump.json` (this is what the tabs expect).
    out_path = root / 'app' / 'features_dump.json'

    model_path = find_model(models_dir)
    if model_path is None:
        print('No model found in', models_dir)
        return

    try:
        m = joblib.load(model_path)
    except Exception as e:
        print('Failed to load model:', e)
        return

    features = []
    if hasattr(m, 'feature_names_in_'):
        features = list(m.feature_names_in_)
    else:
        print('Model lacks feature_names_in_ attribute; aborting')
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(features, fh, ensure_ascii=False, indent=2)
    print('Wrote', out_path)


if __name__ == '__main__':
    main()
