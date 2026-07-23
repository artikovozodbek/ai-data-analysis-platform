import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_filename(filename: str) -> str:
    return Path(filename).name.replace(' ', '_')


def generate_identifier(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]


def dataframe_to_records(df) -> List[Dict[str, Any]]:
    return df.head(20).fillna('').to_dict(orient='records')


def safe_join(base_path: Path, *paths: str) -> Path:
    target = base_path.joinpath(*paths).resolve()
    if base_path not in target.parents and target != base_path:
        raise ValueError('Attempted path traversal in file path creation.')
    return target
