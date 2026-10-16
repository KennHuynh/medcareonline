import pytest
 
from app.config import _database_url
 
 
@pytest.mark.parametrize(
    "given",
    [
        "postgres://u:p@host/db?sslmode=require",
        "postgresql://u:p@host/db?sslmode=require",
    ],
)
def test_postgres_urls_use_installed_psycopg2_driver(monkeypatch, given):
    monkeypatch.setenv("DATABASE_URL", given)
    assert _database_url() == "postgresql+psycopg2://u:p@host/db?sslmode=require"
 
 
def test_other_urls_are_left_alone(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./x.db")
    assert _database_url() == "sqlite:///./x.db"
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@host/db")
    assert _database_url() == "postgresql+psycopg2://u:p@host/db"
