from app.services.config.config_models import TotalConfig
from app.services.config.config_loader import ConfigLoader


# Singleton
class ConfigService:
    _config: TotalConfig

    def __init__(self):
        self._config = ConfigLoader.load_settings("total_config", TotalConfig)

    def get(self) -> TotalConfig:
        return self._config