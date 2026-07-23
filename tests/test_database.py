from pathlib import Path
from database.db import Database


def test_database_register_and_retrieve(tmp_path: Path) -> None:
    db_path = tmp_path / 'app.db'
    database = Database(db_path)
    database.register_dataset('test-id', 'sample.csv', str(tmp_path / 'sample.csv'), {'rows': 2})
    dataset = database.get_dataset('test-id')
    assert dataset is not None
    assert dataset['filename'] == 'sample.csv'
    assert dataset['id'] == 'test-id'
