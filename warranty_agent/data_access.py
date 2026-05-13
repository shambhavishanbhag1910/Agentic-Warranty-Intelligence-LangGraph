from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def load_table(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")
    return pd.read_csv(path)


def find_one(df: pd.DataFrame, **filters):
    subset = df.copy()
    for column, value in filters.items():
        if column not in subset.columns:
            return None
        subset = subset[subset[column].astype(str) == str(value)]
    if subset.empty:
        return None
    return subset.iloc[0].to_dict()


def clean_record(record: dict) -> dict:
    cleaned = {}
    for key, value in record.items():
        if pd.isna(value):
            cleaned[key] = None
        elif hasattr(value, "item"):
            cleaned[key] = value.item()
        else:
            cleaned[key] = value
    return cleaned
