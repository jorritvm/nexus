"""
this file represents an app config parser defined at application level
"""

from pydantic import BaseModel

class AppConfig(BaseModel):
    appcfg_param_defined_in_code: str = "default_value_set_in_code"
    appcfg_param_overwritten_by_cli: srt = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_env: srt = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_env_but_int: int = 0
    appcfg_param_overwritten_by_file: srt = "default_value_set_in_appcfg_code"
    appcfg_param_overwritten_by_runtime_cfg: str = "default_value_set_in_appcfg"

