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
    another_runtime_cfg_param: str = "default_runtime_value"
    a_nullable_runtime_cfg_param: str | None = None

if __name__ == "__main__":
    # # Set the app config (from file or defaults)
    # config.set_app_config(AppConfig, path="src/demo_app/appconfig.yaml")
    # # Set the runtime config (from defaults, or provide a path to a YAML file if available)
    # config.set_runtime_config(RunConfig)
    #
    # # Access individual configs if needed
    # cli_cfg = config.setup_config()
    # print("CLI config:", cli_cfg)

