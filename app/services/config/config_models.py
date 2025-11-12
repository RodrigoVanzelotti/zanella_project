from typing import Optional, List
from pydantic import BaseModel
import os
from app.services.config.env_variables import set_env_variables_from_dotenv
import logging

logger = logging.getLogger(__name__)

set_env_variables_from_dotenv()

def get_development_settings(key, default_value: Optional[str] = None) -> Optional[str]:
    if "APP_TARGET_ENV" not in os.environ:
        logger.error("APP_TARGET_ENV not set in environment variables.")
        exit(1)

    if os.environ["APP_TARGET_ENV"] != "production":
        value = os.environ[key]
        match value:
            case 'true':
                return True
            case 'false':
                return False
            case _:
                return value
    else:
        return default_value
    

class AppConfig(BaseModel):
    name: str
    version: str
    log_level: str
    target_env: str = get_development_settings("APP_TARGET_ENV", "production")
    test_mode: bool = get_development_settings("APP_TEST_MODE", False)

class GoogleConfig(BaseModel):
    api_key: str | bool
    scopes: List[str]
    service_account_file: str | bool



class TotalConfig(BaseModel):
    app: AppConfig
    google: GoogleConfig