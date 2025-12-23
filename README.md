# Nexus
A configuration manager for python code. 

Meant to reduce the amount of developer code needed to get a flexible python application configuration up and running.

<!-- TOC -->
* [Nexus](#nexus)
  * [Features](#features)
  * [Concepts](#concepts)
    * [Configuration levels](#configuration-levels)
    * [Type safety](#type-safety)
    * [Unified configuration model](#unified-configuration-model)
  * [How to use](#how-to-use)
    * [1. Define your configuration models](#1-define-your-configuration-models)
    * [2. Load only defaults from AppConfig](#2-load-only-defaults-from-appconfig)
    * [3. Load defaults from AppConfig and RunConfig (with shared keys)](#3-load-defaults-from-appconfig-and-runconfig-with-shared-keys)
    * [4. Overwrite a default value in code](#4-overwrite-a-default-value-in-code)
    * [5. Overwrite with values from a YAML file](#5-overwrite-with-values-from-a-yaml-file)
    * [6. Overwrite with values from an .env file (including type coercion)](#6-overwrite-with-values-from-an-env-file-including-type-coercion)
    * [7. Overwrite with environment variables (including type coercion)](#7-overwrite-with-environment-variables-including-type-coercion)
    * [8. Overwrite with command line arguments](#8-overwrite-with-command-line-arguments)
    * [9. Full setup in one go (recommended for most use cases)](#9-full-setup-in-one-go-recommended-for-most-use-cases)
    * [10. Accessing the config anywhere](#10-accessing-the-config-anywhere)
    * [11. CLI help output](#11-cli-help-output)
  * [Author](#author)
<!-- TOC -->

## Features

| Feature                                 | Supported |
|-----------------------------------------|:---------:|
| Supports command line arguments         |     ✅     |
| Supports environment variables          |     ✅     |
| Support environment variables from .env files |  ✅  |
| Supports YAML configuration files       |     ✅     |
| Support default values in code          |     ✅     |
| Type safe configuration values          |     ✅     |
| Fail early                              |     ✅     |
| Priority based merge of multiple configuration sources | ✅ |
| Easy to use API                         |     ✅     |
| Support for nested config files         |     ❌     |

## Concepts
### Configuration levels
There are 2 levels of configuration supported by this library.
- Application level configuration: Configuration that is global to the entire application. 
- Runtime level configuration: Configuration that is specific to a particular runtime/entrypoint of the application.

### Type safety
The developer defines pydantic models for the configuration structure. This ensures type safety and validation of configuration values.

### Unified configuration model
Unification happens on 2 levels:
- Application level and runtime level configuration are merged into a single configuration model. Duplicate keys are resolved by giving priority to runtime level configuration.
- Multiple sources are merged into a single unified configuration model. The sources are prioritized in the following order (highest to lowest):
  - Command line arguments
  - Environment variables
  - .env files
  - YAML configuration files
  - Default values in code

## How to use

The `nexus.config` module provides a flexible and type-safe way to manage configuration in your Python applications. You define your configuration structure using Pydantic models, and then use the config API to load, merge, and override configuration values from multiple sources in a clear priority order.

Below are extensive usage examples covering all common scenarios. See `src/demo_app/entrypoint.py` for runnable code.

### 1. Define your configuration models

```python
from pydantic import BaseModel

class AppConfig(BaseModel):
    appcfg_param_defined_in_code: str = "default_value_set_in_code"
    appcfg_param_overwritten_by_cli: str = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_env: str = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_env_but_int: int = 0
    appcfg_param_overwritten_by_file: str = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_runtime_cfg: str = "default_value_set_in_appcfg"

class RunConfig(BaseModel):
    appcfg_param_overwritten_by_runtime_cfg: str = "default_value_set_in_runcfg"
    runcfg_another_param: str = "default_runtime_value"
    runcfg_a_nullable_param: str | None = None
    runcfg_a_value_hardcoded_in_code: str = "default_pydantic_value"
```

---

### 2. Load only defaults from AppConfig

```python
from nexus import config
config.CONFIG = None  # reset config
config.setup_defaults(AppConfig)
print(config.CONFIG.model_dump())
```

---

### 3. Load defaults from AppConfig and RunConfig (with shared keys)

```python
config.CONFIG = None  # reset config
config.setup_defaults(AppConfig, RunConfig)
print(config.CONFIG.model_dump())
```

---

### 4. Overwrite a default value in code

```python
config.CONFIG = None  # reset config
config.setup_defaults(AppConfig, RunConfig, runcfg_a_value_hardcoded_in_code="overwritten_value_set_in_code")
print(config.CONFIG.model_dump())
```

---

### 5. Overwrite with values from a YAML file

```python
config.CONFIG = None  # reset config
config.setup_defaults(AppConfig, RunConfig)
config.setup_file("src/demo_app/appconfig.yaml")
print(config.CONFIG.model_dump())
```

---

### 6. Overwrite with values from an .env file (including type coercion)

```python
config.CONFIG = None  # reset config
config.setup_defaults(AppConfig, RunConfig)
config.setup_file("src/demo_app/appconfig.env")
print(config.CONFIG.model_dump())
```

---

### 7. Overwrite with environment variables (including type coercion)

```python
import os
config.CONFIG = None  # reset config
os.environ["APPCFG_PARAM_OVERWRITTEN_BY_ENV_BUT_INT"] = "2"
config.setup_defaults(AppConfig, RunConfig)
config.setup_file("src/demo_app/appconfig.env")
config.setup_env_vars()
print(config.CONFIG.model_dump())
```

---

### 8. Overwrite with command line arguments

You can pass CLI arguments to your script, e.g.:

```shell
python entrypoint.py --appcfg_param_overwritten_by_cli "cli_value"
```

Or programmatically:

```python
import sys
sys.argv += ["--appcfg_param_overwritten_by_cli", "cli_value"]
config.CONFIG = None  # reset config
config.setup_defaults(AppConfig, RunConfig)
config.setup_file("src/demo_app/appconfig.env")
config.setup_env_vars()
config.setup_cli()
print(config.CONFIG.model_dump())
```

---

### 9. Full setup in one go (recommended for most use cases)

```python
config.CONFIG = None  # reset config
config.setup(AppConfig, RunConfig, path="src/demo_app/appconfig.yaml", env=True, cli=True)
print(config.CONFIG.model_dump())
```

---

### 10. Accessing the config anywhere

After setup, you can import and use `config.CONFIG` or `config.get_config()` from anywhere in your application:

```python
from nexus import config
cfg = config.get_config()
print(cfg.appcfg_param_defined_in_code)
```

---

### 11. CLI help output

The CLI help is automatically generated from your config model fields. Argument placeholders are shown as `VALUE` for clarity:

```shell
python entrypoint.py --help
```

Example output:

```
usage: entrypoint.py [-h] [--appcfg_param_defined_in_code VALUE] [--appcfg_param_overwritten_by_cli VALUE] ...

options:
  -h, --help            show this help message and exit
  --appcfg_param_defined_in_code VALUE
  --appcfg_param_overwritten_by_cli VALUE
  ...
```

---

See `src/demo_app/entrypoint.py` for a full runnable example covering all these cases.

## Author
Jorrit Vander Mynsbrugge