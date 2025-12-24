"""
this file is used to showcase how to use nexus configuration manager
"""

# this represents the entrypoint of an application
from pprint import pprint

from demo_app.app_config import AppConfig
import nexus.config as nx
from nexus import CONFIG
from pydantic import BaseModel

class RunConfig(BaseModel):
    appcfg_param_overwritten_by_runtime_cfg: str = "default_value_set_in_runcfg"
    runcfg_another_param: str = "default_runtime_value"
    runcfg_a_nullable_param: str | None = None
    runcfg_a_value_hardcoded_in_code: str = "default_pydantic_value"
    json_str_param: str = "string from runconfig"
    json_int_param: int = 99
    json_nested_param: str = '{"run": true, "list": [4, 5, 6]}'




if __name__ == "__main__":
    # # testing the nexus config module
    # print("------------------------------------------------------------------")
    # print("This is a config with only defaults from AppConfig:")
    # nx.setup_defaults(AppConfig)
    # pprint(CONFIG.model_dump())
    #
    # print("------------------------------------------------------------------")
    # print("This is a config with defaults from AppConfig and RunConfig, with a shared key:")
    # nx.clear_config() # reset config
    # nx.setup_defaults(AppConfig, RunConfig)
    # pprint(CONFIG.model_dump())
    #
    # print("------------------------------------------------------------------")
    # print("This is a config with a default overwritten by the coder:")
    # nx.clear_config() # reset config
    # nx.setup_defaults(AppConfig, RunConfig, runcfg_a_value_hardcoded_in_code="overwritten_value_set_in_code")
    # pprint(CONFIG.model_dump())
    #
    # print("------------------------------------------------------------------")
    # print("This is a config with a value ingested from a yaml file:")
    # nx.clear_config() # reset config
    # nx.setup_defaults(AppConfig, RunConfig)
    # nx.setup_file("src/demo_app/appconfig.yaml")
    # pprint(CONFIG.model_dump())
    #
    # print("------------------------------------------------------------------")
    # print("This is a config with a value ingested from an env file (and setting an int):")
    # nx.clear_config() # reset config
    # nx.setup_defaults(AppConfig, RunConfig)
    # nx.setup_file("src/demo_app/appconfig.env")
    # pprint(CONFIG.model_dump())
    #
    # print("------------------------------------------------------------------")
    # print("This is a config with an integer environment variable:")
    # import os
    # os.environ["APPCFG_PARAM_OVERWRITTEN_BY_ENV_BUT_INT"] = "2"
    #
    # nx.clear_config() # reset config
    # nx.setup_defaults(AppConfig, RunConfig)
    # nx.setup_file("src/demo_app/appconfig.env")
    # nx.setup_env_vars()
    # pprint(CONFIG.model_dump())
    #
    # print("------------------------------------------------------------------")
    # print("This is a config with a commandline arg: appcfg_param_overwritten_by_cli")
    # nx.clear_config() # reset config
    # nx.setup_defaults(AppConfig, RunConfig)
    # nx.setup_file("src/demo_app/appconfig.env")
    # nx.setup_env_vars()
    # nx.setup_cli()
    # from nexus.config import _CONFIG_EXTENDED
    # print(">>> CONFIG")
    # pprint(CONFIG.model_dump())
    # print(">>> CONFIG_EXTENDED")
    # pprint(_CONFIG_EXTENDED)
    #
    # print("------------------------------------------------------------------")
    # print("This is a config set up in one go")
    # nx.clear_config() # reset config
    # nx.setup(AppConfig, RunConfig, path="src/demo_app/appconfig.yaml", env=True, cli=True)
    # pprint(CONFIG.model_dump())

    print("------------------------------------------------------------------")
    print("Showcase: loading str, int, and nested values from appconfig.json and runconfig")
    nx.clear_config()
    nx.setup_defaults(AppConfig, RunConfig)
    nx.setup_file("src/demo_app/appconfig.json")
    pprint(CONFIG.model_dump())
    print("CONFIG_EXTENDED:")
    pprint(nx.CONFIG_EXTENDED)

    print("done")
