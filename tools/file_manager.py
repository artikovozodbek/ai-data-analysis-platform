import os
import uuid
from pathlib import Path
import pandas as pd
from fastapi import UploadFile
from utils.config import Config
from utils.exceptions import FileError
from utils.helpers import ensure_directory, normalize_filename


def is_allowed_extension(filename: str) -> bool:
    extension = Path(filename).suffix.lower()
    return extension in Config.ALLOWED_EXTENSIONS


def save_dataset(df: pd.DataFrame, path: Path) -> Path:
    path = Path(path)
    suffix = path.suffix.lower()
    try:
        if suffix == '.csv':
            df.to_csv(path, index=False)
        elif suffix in {'.xlsx', '.xls'}:
            df.to_excel(path, index=False)
        elif suffix == '.json':
            df.to_json(path, orient='records')
        elif suffix in {'.txt', '.tsv'}:
            df.to_csv(path, sep='\t', index=False)
        elif suffix == '.parquet':
            df.to_parquet(path, index=False)
        else:
            raise FileError(f'Unsupported dataset format: {suffix}')
    except FileError:
        raise
    except Exception as exc:
        raise FileError(f'Unable to save dataset: {exc}') from exc
    return path


def new_dataset_version_path(upload_dir: Path, original_filename: str, suffix_label: str) -> Path:
    upload_dir = ensure_directory(upload_dir)
    stem = Path(normalize_filename(original_filename)).stem
    extension = Path(original_filename).suffix
    versioned_name = f'{stem}_{suffix_label}{extension}'
    return upload_dir / f'{uuid.uuid4().hex}_{versioned_name}'


def save_upload_file(file: UploadFile, upload_dir: Path) -> Path:
    if not is_allowed_extension(file.filename):
        raise FileError('Unsupported file extension.')
    upload_dir = ensure_directory(upload_dir)
    normalized_name = normalize_filename(file.filename)
    target_path = upload_dir / f"{uuid.uuid4().hex}_{normalized_name}"
    try:
        with target_path.open('wb') as buffer:
            while content := file.file.read(1024 * 1024):
                buffer.write(content)
    except Exception as exc:
        raise FileError(f'Failed to save upload file: {exc}') from exc
    return target_path
