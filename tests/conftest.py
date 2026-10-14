import pytest

from tokentrim import ledger


@pytest.fixture(autouse=True)
def temp_ledger(tmp_path, monkeypatch):
    """Every test writes to a throwaway database, never to data\\ledger.db."""
    monkeypatch.setattr(ledger, "DB_PATH", tmp_path / "test_ledger.db")