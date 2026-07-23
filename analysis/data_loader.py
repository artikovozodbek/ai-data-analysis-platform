from pathlib import Path
import pandas as pd
from typing import List
from utils.config import Config
from utils.exceptions import FileError
from utils.helpers import ensure_directory

SUPPORTED_FORMATS = {'.csv', '.xlsx', '.xls', '.json', '.txt', '.tsv', '.parquet'}

class DataLoader:
    def __init__(self, upload_dir: Path = Config.UPLOAD_DIR):
        self.upload_dir = ensure_directory(upload_dir)

    def load_dataset(self, path: Path) -> pd.DataFrame:
        path = Path(path)
        if not path.exists():
            raise FileError(f'Dataset file not found: {path}')

        suffix = path.suffix.lower()
        try:
            if suffix == '.csv':
                return pd.read_csv(path)
            if suffix in {'.xlsx', '.xls'}:
                return pd.read_excel(path)
            if suffix == '.json':
                return pd.read_json(path)
            if suffix in {'.txt', '.tsv'}:
                return pd.read_csv(path, sep='\t')
            if suffix == '.parquet':
                return pd.read_parquet(path)
            raise FileError(f'Unsupported dataset format: {suffix}')
        except Exception as exc:
            raise FileError(f'Unable to load dataset: {exc}') from exc

    def preview_dataset(self, path: Path, rows: int = 10) -> pd.DataFrame:
        df = self.load_dataset(path)
        return df.head(rows)

    def supported_formats(self) -> List[str]:
        return sorted(SUPPORTED_FORMATS)
