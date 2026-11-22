"""Settings loader: reads config/config.yaml and environment variables (DATABASE_URL)."""
import yaml
import os
from dataclasses import dataclass
from pathlib import Path



@dataclass(frozen=True)
class Settings:
    database_url: str
    config: dict


def load_settings():
    conf_path=Path('config/config.yaml')
    with conf_path.open() as f:
        config = yaml.safe_load(f) or {}

    db_url = os.environ.get("DATABASE_URL")

    return Settings(database_url=db_url, config=config)