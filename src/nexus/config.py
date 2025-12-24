import argparse
import os
from pathlib import Path
import typing
from typing import Type, Any, TYPE_CHECKING

import yaml
from pydantic import BaseModel, create_model

# This module uses a private field that hols the configuration model, and a public proxy CONFIG object.
# This pattern enables from nexus import CONFIG without having to reimport CONFIG when that object is updated.
_CONFIG: BaseModel | None = None # module private field

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

# Stable export that always reflects the latest _CONFIG
CONFIG = ConfigProxy()


# --- PUBLIC API ---
__all__ = [
    "setup",
    "setup_defaults",
    "setup_file",
    "setup_env_vars",
    "setup_cli",
    "clear_config",
    "CONFIG",
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


def setup_defaults(app_model: Type[BaseModel],
                   run_model: Type[BaseModel] | None = None,
                   **kwargs) -> None:
    """
    If run_model is provided, dynamically create a merged config model from app_model and run_model (run_model keys take precedence).
    If not, just instantiate app_model and set global variable _CONFIG.
    Custom values can be passed via kwargs and will take precedence over model defaults.
    """
    global _CONFIG
    if run_model is None:
        # Only pass kwargs that are valid for app_model
        valid_keys = set(app_model.model_fields)
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
        _CONFIG = app_model(**filtered_kwargs)
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


def setup_file(path: str) -> None:
    """
    Overwrite _CONFIG with values from YAML or .env file, enforcing Pydantic validation.
    file_dict values will override existing config values for matching keys.
    """
    global _CONFIG
    if _CONFIG is None:
        raise RuntimeError("Call setup_defaults first.")
    file_dict = _load_config_file(Path(path), _CONFIG)
    # Merge config values explicitly: file_dict values override existing config
    merged_dict = _CONFIG.model_dump() | file_dict
    _CONFIG = _CONFIG.__class__(**merged_dict)


def setup_env_vars() -> None:
    """
    Overwrite _CONFIG with environment variables matching model fields.
    Environment variable values will override existing config values for matching keys.
    Uses Pydantic validation for type coercion.
    """
    global _CONFIG
    if _CONFIG is None:
        raise RuntimeError("Call setup_defaults first.")
    env_dict = _extract_env_vars(_CONFIG)
    # Merge config values explicitly: env_dict values override existing config
    merged_dict = _CONFIG.model_dump() | env_dict
    _CONFIG = _CONFIG.__class__(**merged_dict)


def setup_cli() -> None:
    """
    Overwrite _CONFIG with CLI arguments matching model fields.
    """
    global _CONFIG
    if _CONFIG is None:
        raise RuntimeError("Call setup_defaults first.")
    cli_dict = _extract_cli_args(_CONFIG)
    _CONFIG = _CONFIG.model_copy(update=cli_dict)

def clear_config() -> None:
    """
    Clear the current configuration.
    """
    global _CONFIG
    _CONFIG = None


# --- HELPERS ---

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
