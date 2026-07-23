from pathlib import Path
from fastapi.testclient import TestClient
from main import app


def test_root_redirects_to_ui() -> None:
    client = TestClient(app)
    response = client.get('/')
    assert response.status_code == 200
    assert 'AI Data Analysis Platform' in response.text


def test_settings_endpoint_contains_keys() -> None:
    client = TestClient(app)
    response = client.get('/api/settings')
    assert response.status_code == 200
    json_data = response.json()
    assert 'upload_dir' in json_data
    assert 'db_path' in json_data


def test_upload_endpoint_rejects_missing_file() -> None:
    client = TestClient(app)
    response = client.post('/api/upload', files={})
    assert response.status_code == 422
