import os
from pydantic import BaseModel
import yaml
from typing import Any, Dict, Type, TypeVar, Generic
from app.services.config.env_variables import set_env_variables_from_dotenv

from app.services.config.config_models import TotalConfig

T = TypeVar("T", bound=BaseModel)

class ConfigLoader(Generic[T]):
    @staticmethod
    def _replace_setting_with_env_vars(value: str) -> str:
        if not isinstance(value, str):
            return value
        
        trimmed_value = value.strip()
        if not trimmed_value.startswith("${") or not trimmed_value.endswith("}"):
            return value
        
        inner_content = trimmed_value[2:-1]
        if ":" in inner_content:
            return value
        
        env_var, default = inner_content.split(":", 1)
        return os.environ.get(env_var, default)
    
    @staticmethod
    def _process_config(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in config_dict.items():
            if isinstance(value, dict):
                config_dict[key] = ConfigLoader._process_config(value)
            elif isinstance(value, str):
                config_dict[key] = ConfigLoader._replace_setting_with_env_vars(value)

        return config_dict
    
    @staticmethod
    def load_settings(config_name, cls: Type[T]) -> T:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(os.path.dirname(current_dir))

        config_file = "settings.config.yaml"
        config_path = os.path.join(app_dir, "config", config_file)

        with open(config_path, "r") as file:
            loaded_config = yaml.safe_load(file)
            processed_config = ConfigLoader._process_config(loaded_config)

            return cls.model_validate(processed_config)