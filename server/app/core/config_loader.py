"""
Vendly POS - Configuration Loader
Reads settings from config.yaml file
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml  # type: ignore[import-untyped]


def load_config() -> dict:
    """
    Load configuration from config.yaml
    Falls back to config.example.yaml if config.yaml doesn't exist
    """
    config_paths = [
        Path("config.yaml"),
        Path("config.yml"),
        Path("../config.yaml"),
        Path(__file__).parent.parent.parent.parent / "config.yaml",
    ]

    config_file = None
    for path in config_paths:
        if path.exists():
            config_file = path
            break

    if not config_file:
        # Try example file as fallback for development
        example_path = (
            Path(__file__).parent.parent.parent.parent / "config.example.yaml"
        )
        if example_path.exists():
            print(
                "[WARNING] Using config.example.yaml - copy to config.yaml for production!"
            )
            config_file = example_path
        else:
            return {}

    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a configuration value using dot notation
    Example: get_config("database.host", "localhost")
    """
    config = load_config()
    keys = key.split(".")
    value = config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


def get_database_url() -> str:
    """Build database URL from config"""
    config = load_config()
    db = config.get("database", {})

    # Check environment variable first
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    db_type = db.get("type", "sqlite")

    if db_type == "sqlite":
        path = db.get("path", "./vendly.db")
        return f"sqlite:///{path}"

    elif db_type == "mysql":
        host = db.get("host", "localhost")
        port = db.get("port", 3306)
        name = db.get("name", "vendly_db")
        user = db.get("user", "vendly")
        password = db.get("password", "")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"

    elif db_type == "postgresql":
        host = db.get("host", "localhost")
        port = db.get("port", 5432)
        name = db.get("name", "vendly_db")
        user = db.get("user", "vendly")
        password = db.get("password", "")
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    return "sqlite:///./vendly.db"


def get_store_info() -> dict:
    """Get store information for receipts, etc."""
    config = load_config()
    return config.get(
        "store",
        {
            "name": "Vendly POS",
            "currency": "USD",
        },
    )


def get_tax_settings() -> dict:
    """Get tax configuration"""
    config = load_config()
    return config.get(
        "tax",
        {
            "enabled": True,
            "default_rate": 0.0,
            "tax_name": "Tax",
        },
    )


def get_receipt_settings() -> dict:
    """Get receipt configuration"""
    config = load_config()
    return config.get(
        "receipt",
        {
            "header": "Thank you for shopping!",
            "footer": "Please come again!",
        },
    )


# Export commonly used values
CONFIG = load_config()
