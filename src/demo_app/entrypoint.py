"""
this file is used to showcase how to use nexus configuration manager
"""

# this represents the entrypoint of an application
from pprint import pprint

from demo_app.app_config import AppConfig
from nexus import config
from pydantic import BaseModel

class RunConfig(BaseModel):
    appcfg_param_overwritten_by_runtime_cfg: str = "default_value_set_in_runcfg"
    runcfg_another_param: str = "default_runtime_value"
    runcfg_a_nullable_param: str | None = None
    runcfg_a_value_hardcoded_in_code: str = "default_pydantic_value"

if __name__ == "__main__":
    # testing the nexus config module
    print("------------------------------------------------------------------")
    print("This is a config with only defaults from AppConfig:")
    config.CONFIG = None # reset config
    config.setup_defaults(AppConfig)
    pprint(config.CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("This is a config with defaults from AppConfig and RunConfig, with a shared key:")
    config.CONFIG = None # reset config
    config.setup_defaults(AppConfig, RunConfig)
    pprint(config.CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("This is a config with a default overwritten by the coder:")
    config.CONFIG = None # reset config
    config.setup_defaults(AppConfig, RunConfig, **{"runcfg_a_value_hardcoded_in_code": "overwritten_value_set_in_code"})
    pprint(config.CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("This is a config with a value ingested from a yaml file:")
    config.CONFIG = None # reset config
    config.setup_defaults(AppConfig, RunConfig)
    config.setup_file("src/demo_app/appconfig.yaml")
    pprint(config.CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("This is a config with a value ingested from an env file (and setting an int):")
    config.CONFIG = None # reset config
    config.setup_defaults(AppConfig, RunConfig)
    config.setup_file("src/demo_app/appconfig.env")
    pprint(config.CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("This is a config with an integer environment variable:")
    import os
    os.environ["APPCFG_PARAM_OVERWRITTEN_BY_ENV_BUT_INT"] = "2"
    config.CONFIG = None # reset config
    config.setup_defaults(AppConfig, RunConfig)
    config.setup_file("src/demo_app/appconfig.env")
    config.setup_env_vars()
    pprint(config.CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("This is a config with a commandline arg: appcfg_param_overwritten_by_cli")
    config.CONFIG = None # reset config
    config.setup_defaults(AppConfig, RunConfig)
    config.setup_file("src/demo_app/appconfig.env")
    config.setup_env_vars()
    config.setup_cli()

    x="""this generates a nice cli
    usage: entrypoint.py [-h] [--appcfg_param_defined_in_code APPCFG_PARAM_DEFINED_IN_CODE] [--appcfg_param_overwritten_by_cli APPCFG_PARAM_OVERWRITTEN_BY_CLI] [--appcfg_param_overwritten_by_env APPCFG_PARAM_OVERWRITTEN_BY_ENV] [--appcfg_param_overwritten_by_env_but_int APPCFG_PARAM_OVERWRITTEN_BY_ENV_BUT_INT] [--appcfg_param_overwritten_by_file APPCFG_PARAM_OVERWRITTEN_BY_FILE]
                     [--appcfg_param_overwritten_by_runtime_cfg APPCFG_PARAM_OVERWRITTEN_BY_RUNTIME_CFG] [--runcfg_another_param RUNCFG_ANOTHER_PARAM] [--runcfg_a_nullable_param RUNCFG_A_NULLABLE_PARAM] [--runcfg_a_value_hardcoded_in_code RUNCFG_A_VALUE_HARDCODED_IN_CODE]

    options:
      -h, --help            show this help message and exit
      --appcfg_param_defined_in_code APPCFG_PARAM_DEFINED_IN_CODE
      --appcfg_param_overwritten_by_cli APPCFG_PARAM_OVERWRITTEN_BY_CLI
      --appcfg_param_overwritten_by_env APPCFG_PARAM_OVERWRITTEN_BY_ENV
      --appcfg_param_overwritten_by_env_but_int APPCFG_PARAM_OVERWRITTEN_BY_ENV_BUT_INT
      --appcfg_param_overwritten_by_file APPCFG_PARAM_OVERWRITTEN_BY_FILE
      --appcfg_param_overwritten_by_runtime_cfg APPCFG_PARAM_OVERWRITTEN_BY_RUNTIME_CFG
      --runcfg_another_param RUNCFG_ANOTHER_PARAM
      --runcfg_a_nullable_param RUNCFG_A_NULLABLE_PARAM
      --runcfg_a_value_hardcoded_in_code RUNCFG_A_VALUE_HARDCODED_IN_CODE
    """
    pprint(config.CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("This is a config set up in one go")
    config.CONFIG = None # reset config
    config.setup(AppConfig, RunConfig, path="src/demo_app/appconfig.yaml", env=True, cli=True)
    pprint(config.CONFIG.model_dump())





    print("done")