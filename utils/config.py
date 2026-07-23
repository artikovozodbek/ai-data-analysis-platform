from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

class Config:
    BASE_DIR = Path(__file__).resolve().parent.parent
    UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', BASE_DIR / 'uploads'))
    LOG_DIR = Path(os.getenv('LOG_DIR', BASE_DIR / 'logs'))
    DB_PATH = Path(os.getenv('DB_PATH', BASE_DIR / 'database' / 'app.db'))
    ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json', '.txt', '.tsv', '.parquet'}
    MAX_UPLOAD_SIZE = int(os.getenv('MAX_UPLOAD_SIZE', str(50 * 1024 * 1024)))
    API_PREFIX = os.getenv('API_PREFIX', '/api')
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',') if os.getenv('CORS_ORIGINS') else ['*']
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()
    DATA_RETENTION_DAYS = int(os.getenv('DATA_RETENTION_DAYS', '30'))
    REPORTS_DIR = Path(os.getenv('REPORTS_DIR', BASE_DIR / 'reports'))
    UI_DIR = Path(os.getenv('UI_DIR', BASE_DIR / 'ui'))
