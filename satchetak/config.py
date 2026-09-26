from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _load_env_file(path: Path) -> None:
    """Load a small, predictable .env subset without overriding process variables."""
    if not path.is_file():
        return
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ValueError(f"Invalid environment entry at {path}:{line_number}")
        key, value = (part.strip() for part in line.split("=", 1))
        if not _ENV_KEY.fullmatch(key):
            raise ValueError(f"Invalid environment key at {path}:{line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'\"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


_configured_env_file = Path(os.environ.get("SATCHETAK_ENV_FILE", ROOT / ".env"))
_load_env_file(_configured_env_file)


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.environ.get("SATCHETAK_DATA_DIR", ROOT / "data"))
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.environ.get(
            "SATCHETAK_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    )
    cdse_client_id: str | None = os.environ.get("CDSE_CLIENT_ID")
    cdse_client_secret: str | None = os.environ.get("CDSE_CLIENT_SECRET")
    qwen_base_url: str | None = os.environ.get("QWEN_BASE_URL")
    qwen_model: str = os.environ.get("QWEN_MODEL", "qwen2.5:1.5b")
    qwen_api_key: str = os.environ.get("QWEN_API_KEY", "EMPTY")
    bhoonidhi_user_id: str | None = os.environ.get("BHOONIDHI_USER_ID")
    bhoonidhi_password: str | None = os.environ.get("BHOONIDHI_PASSWORD")
    bhoonidhi_collection: str | None = os.environ.get("BHOONIDHI_COLLECTION")
    planetary_computer_enabled: bool = os.environ.get("PLANETARY_COMPUTER_ENABLED", "true").lower() in {"1", "true", "yes"}
    bhuvan_wms_url: str | None = os.environ.get("BHUVAN_WMS_URL")
    bhuvan_wms_layer: str | None = os.environ.get("BHUVAN_WMS_LAYER")


settings = Settings()
