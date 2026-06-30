from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_local_compose_exposes_postgres_and_redis_on_loopback_only() -> None:
    compose = (ROOT / "docker-compose.local.yml").read_text()

    assert "127.0.0.1:5432:5432" in compose
    assert "127.0.0.1:6379:6379" in compose
    assert "0.0.0.0:5432" not in compose
    assert "0.0.0.0:6379" not in compose


def test_host_compose_exposes_nginx_on_loopback_only() -> None:
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "127.0.0.1:8080:80" in compose
    assert "0.0.0.0:8080:80" not in compose
    assert '"8080:80"' not in compose


def test_readme_documents_local_postgres_connection() -> None:
    readme = (ROOT / "README.md").read_text()

    assert "docker-compose.local.yml" in readme
    assert "cp .env.local.example .env" in readme


def test_local_env_example_uses_host_postgres_connection() -> None:
    env_example = (ROOT / ".env.local.example").read_text()

    assert "POSTGRES_HOST=localhost" in env_example
    assert "POSTGRES_PORT=5432" in env_example
    assert "REDIS_URL=redis://localhost:6379/0" in env_example
