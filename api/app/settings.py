import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _list(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("DATA_DIR", ROOT / "data")))
    # Browsers may only call the API from these origins (the web app).
    allowed_origins: list[str] = field(default_factory=lambda: _list("ALLOWED_ORIGINS", "http://localhost:3000"))
    # Shared secret the Next.js server sends along with the visitor's IP, so
    # rate limits apply per visitor instead of per Vercel server.
    proxy_key: str = field(default_factory=lambda: os.environ.get("PROXY_KEY", ""))
    trust_forwarded_for: bool = field(default_factory=lambda: os.environ.get("TRUST_FORWARDED_FOR", "0") == "1")
    rate_per_minute: int = field(default_factory=lambda: int(os.environ.get("RATE_PER_MINUTE", "90")))
    rate_burst: int = field(default_factory=lambda: int(os.environ.get("RATE_BURST", "30")))
    enable_docs: bool = field(default_factory=lambda: os.environ.get("ENABLE_DOCS", "0") == "1")


def get_settings() -> Settings:
    return Settings()
