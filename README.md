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
    * [Dynamic Configuration Access with a Stable Proxy](#dynamic-configuration-access-with-a-stable-proxy)
    * [Package-Level API Convenience](#package-level-api-convenience)
  * [How to use](#how-to-use)
    * [1. Define your configuration models and imports](#1-define-your-configuration-models-and-imports)
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
  * [Todo](#todo)
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

## Minimal example
Code:
```python
import nexus as nx
from nexus import CONFIG
from pydantic import BaseModel

class MyConfiguration(BaseModel):
    some_parameter: str = "default_value_set_in_python_code"
    another_parameter: str = "default_value_set_in_python_code"

nx.setup(MyConfiguration, cli=True)
print(CONFIG.model_dump())
```
Execution:
```commandline
python test_nexus.py --another_parameter set_from_cli 
{'some_parameter': 'default_value_set_in_python_code', 'another_parameter': 'set_from_cli'}
```




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

### Dynamic Configuration Access with a Stable Proxy

A common challenge in Python configuration management is ensuring that the configuration object you import always 
reflects the latest state, especially when it can be updated at runtime. Typically, when you import a module-level 
field e.g., `from nx import CONFIG`, Python saves a reference to the object as it was at import time. If the module 
later updates that object, your imported reference does not automatically update, which can lead to stale or 
inconsistent configuration in your application.

One workaround is to provide a `get()` method (e.g., `nx.get_config()`), but this adds boilerplate and is less 
ergonomic for the client. Another approach is to always access the configuration via the module itself 
(e.g., `nx.CONFIG`), which ensures you get the latest value, but this also adds extra characters and is less convenient.

Nexus solves this by exporting a stable proxy object as `CONFIG`. This proxy always delegates attribute access to 
the current configuration instance, so `from nexus.config import CONFIG` will always give you the latest configuration,
even if it is updated after import. This design combines convenience and correctness, allowing you to write clean, 
idiomatic code without worrying about stale references or extra boilerplate.

### Package-Level API Convenience
For maximum convenience, the entire public API of the `config` module is also exposed directly at the package level. 
This means you can simply `import nexus as nx` and access all configuration setup and access methods directly, 
such as `nx.setup()`, without needing to reference the submodule `nx.config.setup()`. 


## How to use

The `nexus.config` module provides a flexible and type-safe way to manage configuration in your Python applications. 
You define your configuration structure using Pydantic models, and then use the config API to load, merge, and override 
configuration values from multiple sources in a clear priority order.

Below are extensive usage examples covering all common scenarios. See `src/demo_app/entrypoint.py` for runnable code.

### 1. Define your configuration models and imports
You can isolate a general application configuration model into a separate file that can be imported anywhere in your application.
```python
# app_configuration.py
from pydantic import BaseModel

class AppConfig(BaseModel):
    appcfg_param_defined_in_code: str = "default_value_set_in_code"
    appcfg_param_overwritten_by_cli: str = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_env: str = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_env_but_int: int = 0
    appcfg_param_overwritten_by_file: str = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_runtime_cfg: str = "default_value_set_in_appcfg"
```

In your entrypoint you can define a runtime specific configuration model. Here you must also define all imports.
```python
# demo.py - a entrypoint specific configuration
import nexus as nx
from nexus import CONFIG
from pydantic import BaseModel

class RunConfig(BaseModel):
    appcfg_param_overwritten_by_runtime_cfg: str = "default_value_set_in_runcfg"
    runcfg_another_param: str = "default_runtime_value"
    runcfg_a_nullable_param: str | None = None
    runcfg_a_value_hardcoded_in_code: str = "default_pydantic_value"
```

---

### 2. Load only defaults from AppConfig

```python
nx.setup_defaults(AppConfig)
print(CONFIG.model_dump())
```

---

### 3. Load defaults from AppConfig and RunConfig (with shared keys)

```python
nx.setup_defaults(AppConfig, RunConfig)
print(CONFIG.model_dump())
```

---

### 4. Overwrite a default value in code

```python
nx.setup_defaults(AppConfig, RunConfig, runcfg_a_value_hardcoded_in_code="overwritten_value_set_in_code")
print(CONFIG.model_dump())
```

---

### 5. Overwrite with values from a YAML file

```python
nx.setup_defaults(AppConfig, RunConfig)
nx.setup_file("src/demo_app/appconfig.yaml")
print(CONFIG.model_dump())
```

---

### 6. Overwrite with values from an .env file (including type coercion)

```python
nx.setup_defaults(AppConfig, RunConfig)
nx.setup_file("src/demo_app/appconfig.env")
print(CONFIG.model_dump())
```

---

### 7. Overwrite with environment variables (including type coercion)

```python
import os
os.environ["APPCFG_PARAM_OVERWRITTEN_BY_ENV_BUT_INT"] = "2"

nx.setup_defaults(AppConfig, RunConfig)
nx.setup_file("src/demo_app/appconfig.env")
nx.setup_env_vars()
print(CONFIG.model_dump())
```

---

### 8. Overwrite with command line arguments

You can pass CLI arguments to your script, e.g.:

```shell
python demo.py --appcfg_param_overwritten_by_cli "cli_value"
```

Or programmatically:

```python
import sys
sys.argv += ["--appcfg_param_overwritten_by_cli", "cli_value"]

nx.setup_defaults(AppConfig, RunConfig)
nx.setup_file("src/demo_app/appconfig.env")
nx.setup_env_vars()
nx.setup_cli()
print(CONFIG.model_dump())
```

---

### 9. Full setup in one go (recommended for most use cases)

```python
nx.setup(AppConfig, RunConfig, path="src/demo_app/appconfig.yaml", env=True, cli=True)
print(CONFIG.model_dump())
```

---

### 10. Accessing the config anywhere

After setup, you can import and use `config.CONFIG` from anywhere in your application:

```python
from nexus.config import CONFIG
print(CONFIG.appcfg_param_defined_in_code)
```

---

### 11. CLI help output

The CLI help is automatically generated from your config model fields. Argument placeholders are shown as `VALUE` for clarity:

```shell
python demo.py --help
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

## Configuration traceability
To track the source of the configuration value, a second dictionary `CONFIG_EXTENDED` is available after setup.
This dictionary contains tuples of (value, source), where source indicates where the value originated from.

```commandline
>>> CONFIG
{'appcfg_param_defined_in_code': 'default_value_set_in_code',
 'appcfg_param_overwritten_by_cli': 'set_by_cli',
 'appcfg_param_overwritten_by_env': 'default_value_set_in_appcfg_code',
 'appcfg_param_overwritten_by_env_but_int': 1,
 'appcfg_param_overwritten_by_file': 'value_set_in_env_file',
 'appcfg_param_overwritten_by_runtime_cfg': 'default_value_set_in_runcfg',
 'runcfg_a_nullable_param': None,
 'runcfg_a_value_hardcoded_in_code': 'default_pydantic_value',
 'runcfg_another_param': 'default_runtime_value'}
>>> CONFIG_EXTENDED
{'appcfg_param_defined_in_code': ('default_value_set_in_code',
                                  SET_BY_DEFAULT_APP_CONFIG),
 'appcfg_param_overwritten_by_cli': ('set_by_cli', SET_BY_CLI),
 'appcfg_param_overwritten_by_env': ('default_value_set_in_appcfg_code',
                                     SET_BY_DEFAULT_APP_CONFIG),
 'appcfg_param_overwritten_by_env_but_int': (1,
                                             (SET_BY_ENV_FILE,
                                              'src/demo_app/appconfig.env')),
 'appcfg_param_overwritten_by_file': ('value_set_in_env_file',
                                      (SET_BY_ENV_FILE,
                                       'src/demo_app/appconfig.env')),
 'appcfg_param_overwritten_by_runtime_cfg': ('default_value_set_in_runcfg',
                                             SET_BY_DEFAULT_RUN_CONFIG),
 'runcfg_a_nullable_param': (None, SET_BY_DEFAULT_RUN_CONFIG),
 'runcfg_a_value_hardcoded_in_code': ('default_pydantic_value',
                                      SET_BY_DEFAULT_RUN_CONFIG),
 'runcfg_another_param': ('default_runtime_value', SET_BY_DEFAULT_RUN_CONFIG)}
 ```

## Author
Jorrit Vander Mynsbrugge