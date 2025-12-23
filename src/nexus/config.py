import argparse
from pathlib import Path
from typing import Type, Optional
import typing
import os

import yaml
from pydantic import BaseModel, create_model

_app_config_instance: BaseModel | None = None
_runtime_config_instance: BaseModel | None = None

__all__ = [
    "create_default_app_config",
    "create_default_runtime_config",
    "set_app_config_file",
    "set_runtime_config_file",
]


# ++++++  PUBLIC API ++++++ #


# ++++++  HELPER FUNCTIONS ++++++ #

def _load_env_file(path: Path) -> dict:
    """
    Load a .env file and return a dict with lowercase keys.
    """
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


def _load_config_file(path: Path) -> dict:
    """
    Load config values from a YAML or .env file, with .env values overriding YAML if both exist.
    """
    config_dict = {}
    if path.suffix in {".yaml", ".yml"}:
        with path.open("r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f) or {}
    elif path.suffix == ".env":
        config_dict = _load_env_file(path)
    return config_dict


def _set_config_instance(model: Type[BaseModel], path: Optional[str]) -> BaseModel:
    """
    Common logic for loading config from YAML or .env and instantiating the model.
    """
    config_dict = {}
    if path:
        _path = Path(path)
        if not _path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        if _path.suffix in {".yaml", ".yml"}:
            config_dict = _load_config_file(_path)
        elif _path.suffix == ".env":
            config_dict = _load_env_file(_path)
        else:
            raise ValueError(f"Unsupported config file extension: {path}")
    # Lowercase keys for .env, match to model fields
    model_fields = {f.lower(): f for f in model.model_fields}
    normalized = {model_fields.get(k.lower(), k): v for k, v in (config_dict or {}).items()}
    return model(**normalized) if normalized else model()


def create_default_app_config(model: Type[BaseModel]) -> BaseModel:
    """
    Create an app config instance with default values only.
    """
    return model()


def create_default_runtime_config(model: Type[BaseModel]) -> BaseModel:
    """
    Create a runtime config instance with default values only.
    """
    return model()


def set_app_config_file(model: Type[BaseModel], path: str) -> None:
    """
    Set the application config model by loading from a YAML or .env file.
    """
    global _app_config_instance
    _app_config_instance = _set_config_instance(model, path)


def set_runtime_config_file(model: Type[BaseModel], path: str) -> None:
    """
    Set the runtime config model by loading from a YAML or .env file.
    """
    global _runtime_config_instance
    _runtime_config_instance = _set_config_instance(model, path)


def get_app_config() -> BaseModel:
    """
    Retrieve the current application config instance.
    """
    if _app_config_instance is None:
        raise RuntimeError("App config has not been set. Call set_app_config first.")
    return _app_config_instance


def get_runtime_config() -> BaseModel:
    """
    Retrieve the current runtime config instance.
    """
    if _runtime_config_instance is None:
        raise RuntimeError("Runtime config has not been set. Call set_runtime_config first.")
    return _runtime_config_instance


def merge_configs(app: BaseModel, run: BaseModel):
    """
    Merge app and runtime configs into a new Pydantic model class and a merged dict, with runtime config taking precedence.
    Returns (MergedConfigClass, merged_dict)
    """
    app_dict = app.model_dump()
    run_dict = run.model_dump()
    merged_dict = {**app_dict, **run_dict}  # run_dict values override app_dict

    # Collect fields from both models, with run fields taking precedence
    app_fields = app.__class__.__annotations__
    run_fields = run.__class__.__annotations__
    merged_fields = {**app_fields, **run_fields}  # run_fields override app_fields

    # Collect default values
    app_defaults = {k: getattr(app, k, None) for k in app_fields}
    run_defaults = {k: getattr(run, k, None) for k in run_fields}
    merged_defaults = {**app_defaults, **run_defaults}

    # Build field definitions for create_model
    field_definitions = {}
    for k, v in merged_fields.items():
        default = merged_defaults.get(k, ...)
        field_definitions[k] = (v, default)

    MergedConfig = create_model("MergedConfig", **field_definitions)  # type: ignore
    return MergedConfig, merged_dict


def get_merged_config():
    """
    Get the merged config as (MergedConfigClass, merged_dict), with runtime config values taking precedence.
    """
    if _app_config_instance is None:
        raise RuntimeError("App config has not been set.")
    if _runtime_config_instance is None:
        raise RuntimeError("Runtime config has not been set.")
    return merge_configs(_app_config_instance, _runtime_config_instance)


# ++++++  POPULATE ARGS PARSER AND OVERLAP ++++++ #
def _get_argparse_type(annotation):
    """
    Given a type annotation, return a type suitable for argparse's type argument.
    For Union types (including Optional), return the first non-None type.
    Default to str if ambiguous.
    """
    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = typing.get_args(annotation)
        # Return the first non-None type
        for arg in args:
            if arg is not type(None):
                return arg
        return str
    if isinstance(annotation, type):
        return annotation
    return str


def add_model(parser, model):
    "Add Pydantic model to an ArgumentParser"
    fields = model.model_fields
    for name, field in fields.items():
        arg_type = _get_argparse_type(field.annotation)
        parser.add_argument(
            f"--{name}",
            dest=name,
            type=arg_type,
            default=field.default,
            help=field.description,
        )


def _extract_env_vars(model, base_dict=None):
    """
    Extract environment variables matching model fields (case-insensitive, underscores),
    and cast to the correct type. base_dict is used for type inference.
    """
    env_dict = {}
    fields = model.model_fields
    for name, field in fields.items():
        env_key = name.upper()
        if env_key in os.environ:
            value = os.environ[env_key]
            # Try to cast to the correct type
            typ = field.annotation
            try:
                # Use the same type logic as argparse
                cast_type = _get_argparse_type(typ)
                env_dict[name] = cast_type(value)
            except Exception:
                env_dict[name] = value
    return env_dict


def get_config(pydantic_model, defaults=None):
    parser = argparse.ArgumentParser()
    add_model(parser, pydantic_model)
    args = parser.parse_args()
    cli_dict = vars(args)
    # Merge CLI args over defaults
    if defaults:
        merged = {**defaults, **{k: v for k, v in cli_dict.items() if v is not None}}
    else:
        merged = cli_dict
    config = pydantic_model(**merged)
    return config


def setup_config():
    MergedConfig, merged_dict = get_merged_config()
    # 1. YAML/.env already in merged_dict
    # 2. Merge in environment variables
    env_dict = _extract_env_vars(MergedConfig, merged_dict)
    merged_with_env = {**merged_dict, **env_dict}
    # 3. Merge in CLI args (highest priority)
    cli_cfg = get_config(MergedConfig, defaults=merged_with_env)
    return cli_cfg


def get(model: Type[BaseModel], cli: bool = True, env: bool = True, path: str = None) -> BaseModel:
    """
    Unified config loader. Priority: CLI > ENV > .env/YAML > defaults.
    Args:
        model: The Pydantic model class.
        cli: Whether to merge in CLI arguments (highest priority).
        env: Whether to merge in environment variables.
        path: Optional path to a YAML or .env file.
    Returns:
        An instance of the model with all sources merged in correct priority.
    """
    # 1. Start with defaults
    config_dict = {}
    # 2. Merge in file config if path is provided
    if path:
        _path = Path(path)
        if not _path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        if _path.suffix in {".yaml", ".yml"}:
            config_dict = _load_config_file(_path)
        elif _path.suffix == ".env":
            config_dict = _load_env_file(_path)
        else:
            raise ValueError(f"Unsupported config file extension: {path}")
        # Normalize keys for .env
        model_fields = {f.lower(): f for f in model.model_fields}
        config_dict = {model_fields.get(k.lower(), k): v for k, v in (config_dict or {}).items()}
    # 3. Merge in environment variables
    if env:
        env_dict = _extract_env_vars(model)
        config_dict = {**config_dict, **env_dict}
    # 4. Merge in CLI args
    if cli:
        parser = argparse.ArgumentParser()
        add_model(parser, model)
        args = parser.parse_args()
        cli_dict = {k: v for k, v in vars(args).items() if v is not None}
        config_dict = {**config_dict, **cli_dict}
    # 5. Instantiate model with merged config
    return model(**config_dict)
