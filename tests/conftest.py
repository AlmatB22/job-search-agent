import pytest


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Point every test at its own empty SQLite file."""
    monkeypatch.setenv("JSA_DB_PATH", str(tmp_path / "jsa.sqlite"))
