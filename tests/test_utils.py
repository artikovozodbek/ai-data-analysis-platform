from pathlib import Path
from utils.helpers import ensure_directory, normalize_filename, generate_identifier


def test_ensure_directory_creates_path(tmp_path: Path) -> None:
    target = tmp_path / 'nested' / 'uploads'
    result = ensure_directory(target)
    assert result.exists() and result.is_dir()


def test_normalize_filename_replaces_spaces() -> None:
    assert normalize_filename('My File.csv') == 'My_File.csv'


def test_generate_identifier_length() -> None:
    identifier = generate_identifier('sample-value')
    assert isinstance(identifier, str)
    assert len(identifier) == 24
