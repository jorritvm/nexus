"""Configuration management module using Pydantic models."""

import argparse
import os
from pathlib import Path
import typing
from typing import Type, Any, TYPE_CHECKING
from enum import Enum

import yaml
from pydantic import BaseModel, create_model

# This module uses a private field that hols the configuration model, and a public proxy CONFIG object.
# This pattern enables from nexus import CONFIG without having to reimport CONFIG when that object is updated.
class ConfigSource(Enum):
    SET_BY_DEFAULT_APP_CONFIG = "set_by_default_app_config"
    SET_BY_DEFAULT_RUN_CONFIG = "set_by_default_run_config"
    SET_BY_DEVELOPER = "set_by_developer"
    SET_BY_YAML_FILE = "set_by_yaml_file"
    SET_BY_ENV_FILE = "set_by_env_file"
    SET_BY_ENVIRONMENT = "set_by_environment"
    SET_BY_CLI = "set_by_cli"

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return str(self)

class ConfigProxy:
    def __getattr__(self, name: str) -> Any:
        if _CONFIG is None:
            raise RuntimeError("CONFIG is not initialized. Call setup_defaults/setup first.")
        return getattr(_CONFIG, name)

    def __repr__(self) -> str:
        return f"<CONFIG proxy -> {_CONFIG!r}>"

if TYPE_CHECKING:
    # Help IDEs/type-checkers understand the public shape
    CONFIG: BaseModel  # type: ignore[no-redef]
    CONFIG_EXTENDED: dict[str, tuple[Any, ConfigSource | tuple[ConfigSource, str]]]

# Stable export that always reflects the latest _CONFIG
_CONFIG: BaseModel | None = None # module private field
_CONFIG_EXTENDED: dict[str, tuple[Any, ConfigSource | tuple[ConfigSource, str]]] = {}  # field -> (value, source or (source, path))
CONFIG = ConfigProxy()
CONFIG_EXTENDED = _CONFIG_EXTENDED

# --- PUBLIC API ---
__all__ = [
    "setup",
    "setup_defaults",
    "setup_file",
    "setup_env_vars",
    "setup_cli",
    "clear_config",
    "CONFIG",
    "CONFIG_EXTENDED",
    ]

def setup(app_model: Type[BaseModel],
          run_model: Type[BaseModel] | None = None,
          path: str | None = None,
          env: bool = True,
          cli: bool = True) -> None:
    """
    Setup config all in one go, merging in order:
    defaults < file (yaml or env) < env vars < CLI
    If run_model is provided, its keys override app_model keys.
    Updates _CONFIG.
    """
    setup_defaults(app_model, run_model)
    if path:
        setup_file(path)
    if env:
        setup_env_vars()
    if cli:
        setup_cli()
    # After all, update extended
    _update_config_extended(_CONFIG, source=None)


def setup_defaults(app_model: Type[BaseModel],
                   run_model: Type[BaseModel] | None = None,
                   **kwargs) -> None:
    """
    If run_model is provided, dynamically create a merged config model from app_model and run_model (run_model keys take precedence).
    If not, just instantiate app_model and set global variable _CONFIG.
    Custom values can be passed via kwargs and will take precedence over model defaults.
    """
    global _CONFIG
    global _CONFIG_EXTENDED
    if run_model is None:
        # Only pass kwargs that are valid for app_model
        valid_keys = set(app_model.model_fields)
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
        _CONFIG = app_model(**filtered_kwargs)
        _CONFIG_EXTENDED.clear()
        for k in app_model.model_fields:
            if k in filtered_kwargs:
                _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEVELOPER)
            else:
                _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEFAULT_APP_CONFIG)
        return
    # For merged model, merge app_model defaults, run_model defaults, then kwargs
    app_fields = app_model.model_fields
    app_ann = app_model.__annotations__
    app_defaults = {k: getattr(app_model(), k, None) for k in app_fields}
    run_fields = run_model.model_fields
    run_ann = run_model.__annotations__
    run_defaults = {k: getattr(run_model(), k, None) for k in run_fields}
    merged_ann = {**app_ann, **run_ann}
    merged_defaults = {**app_defaults, **run_defaults, **kwargs}  # kwargs take highest priority
    field_definitions = {}
    for k, typ in merged_ann.items():
        default = merged_defaults.get(k, ...)
        field_definitions[k] = (typ, default)
    MergedConfig = create_model("MergedConfig", **field_definitions)  # type: ignore
    _CONFIG = MergedConfig()
    _CONFIG_EXTENDED.clear()
    for k in merged_ann:
        if k in kwargs:
            _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEVELOPER)
        elif k in run_defaults and (k not in app_defaults or run_defaults[k] != app_defaults.get(k)):
            _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEFAULT_RUN_CONFIG)
        else:
            _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEFAULT_APP_CONFIG)


def setup_file(path: str) -> None:
    """
    Overwrite _CONFIG with values from YAML or .env file, enforcing Pydantic validation.
    file_dict values will override existing config values for matching keys.
    """
    global _CONFIG
    global _CONFIG_EXTENDED
    if _CONFIG is None:
        raise RuntimeError("Call setup_defaults first.")
    file_dict = _load_config_file(Path(path), _CONFIG)
    # Merge config values explicitly: file_dict values override existing config
    merged_dict = _CONFIG.model_dump() | file_dict
    _CONFIG = _CONFIG.__class__(**merged_dict)
    # Update extended: for each key in file_dict, set source to yaml_file or env_file
    file_source = (ConfigSource.SET_BY_YAML_FILE, path) if Path(path).suffix in {".yaml", ".yml"} else (ConfigSource.SET_BY_ENV_FILE, path)
    for k in file_dict:
        _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), file_source)
    # For other keys, keep previous source
    for k in _CONFIG.model_fields:
        if k not in file_dict and k not in _CONFIG_EXTENDED:
            _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEFAULT_APP_CONFIG)


def setup_env_vars() -> None:
    """
    Overwrite _CONFIG with environment variables matching model fields.
    Environment variable values will override existing config values for matching keys.
    Uses Pydantic validation for type coercion.
    """
    global _CONFIG
    global _CONFIG_EXTENDED
    if _CONFIG is None:
        raise RuntimeError("Call setup_defaults first.")
    env_dict = _extract_env_vars(_CONFIG)
    # Merge config values explicitly: env_dict values override existing config
    merged_dict = _CONFIG.model_dump() | env_dict
    _CONFIG = _CONFIG.__class__(**merged_dict)
    # Update extended: for each key in env_dict, set source to environment
    for k in env_dict:
        _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_ENVIRONMENT)
    # For other keys, keep previous source
    for k in _CONFIG.model_fields:
        if k not in env_dict and k not in _CONFIG_EXTENDED:
            _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEFAULT_APP_CONFIG)


def setup_cli() -> None:
    """
    Overwrite _CONFIG with CLI arguments matching model fields.
    """
    global _CONFIG
    global _CONFIG_EXTENDED
    if _CONFIG is None:
        raise RuntimeError("Call setup_defaults first.")
    cli_dict = _extract_cli_args(_CONFIG)
    _CONFIG = _CONFIG.model_copy(update=cli_dict)
    # Update extended: for each key in cli_dict, set source to cli
    for k in cli_dict:
        _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_CLI)
    # For other keys, keep previous source
    for k in _CONFIG.model_fields:
        if k not in cli_dict and k not in _CONFIG_EXTENDED:
            _CONFIG_EXTENDED[k] = (getattr(_CONFIG, k), ConfigSource.SET_BY_DEFAULT_APP_CONFIG)

def clear_config() -> None:
    """
    Clear the current configuration.
    """
    global _CONFIG
    global _CONFIG_EXTENDED
    _CONFIG = None
    _CONFIG_EXTENDED.clear()


# --- HELPERS ---
def _update_config_extended(model: BaseModel | None, source: ConfigSource | None = None) -> None:
    """
    Helper to update _CONFIG_EXTENDED for all fields in the model.
    If source is given, all fields are marked with that source.
    If not, do not overwrite existing sources.
    """
    global _CONFIG_EXTENDED
    if model is None:
        _CONFIG_EXTENDED.clear()
        return
    for k in model.model_fields:
        if source:
            _CONFIG_EXTENDED[k] = (getattr(model, k), source)
        elif k not in _CONFIG_EXTENDED:
            _CONFIG_EXTENDED[k] = (getattr(model, k), ConfigSource.SET_BY_DEFAULT_APP_CONFIG)


def _load_config_file(path: Path, model: BaseModel) -> dict:
    config_dict = {}
    if path.suffix in {".yaml", ".yml"}:
        with path.open("r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}
    elif path.suffix == ".env":
        config_dict = _load_env_file(path)
    # Normalize keys to match model fields (case-insensitive)
    model_fields = {f.lower(): f for f in model.model_fields}
    normalized = {model_fields.get(k.lower(), k): v for k, v in (config_dict or {}).items()}
    return normalized


def _load_env_file(path: Path) -> dict:
    env_dict = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip().lower()] = value.strip()
    return env_dict


def _extract_env_vars(model: BaseModel) -> dict:
    env_dict = {}
    for name in model.model_fields:
        env_key = name.upper()
        if env_key in os.environ:
            env_dict[name] = os.environ[env_key]
    return env_dict


def _extract_cli_args(model: BaseModel) -> dict:
    parser = argparse.ArgumentParser()
    for name, field in model.model_fields.items():
        arg_type = _get_argparse_type(field.annotation)
        parser.add_argument(
            f"--{name}",
            dest=name,
            type=arg_type,
            default=None,
            help=field.description,
            metavar="VALUE",
            )
    args = parser.parse_args()
    cli_dict = {k: v for k, v in vars(args).items() if v is not None}
    return cli_dict


def _get_argparse_type(annotation):
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = typing.get_args(annotation)
        for arg in args:
            if arg is not type(None):
                return arg
        return str
    if isinstance(annotation, type):
        return annotation
    return str
