import json
import os
from pathlib import Path

DEFAULT_CONFIG_PATH = Path(__file__).parent / "dwiw_config.json"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Environment variables as fallback for API keys
    _resolve_env_vars(config)
    return config


def _resolve_env_vars(config: dict):
    """Replace empty or missing API keys with environment variables."""
    env_map = {
        "claude": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "local":  "LM_STUDIO_API_KEY",
    }
    for backend, env_var in env_map.items():
        if backend in config:
            if not config[backend].get("api_key"):
                config[backend]["api_key"] = os.environ.get(env_var, "")


def get_backend(config: dict, override: str | None = None) -> tuple[str, dict]:
    """
    Returns (backend_name, backend_config).
    Uses override if provided, otherwise falls back to default_backend from config.
    """
    name = override if override else config.get("default_backend", "claude")
    if name not in config:
        raise ValueError(
            f"Backend '{name}' not defined in config. "
            f"Available: {[k for k in config if isinstance(config[k], dict)]}"
        )
    return name, config[name]
