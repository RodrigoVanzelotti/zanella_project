import punq
from app.services.config.config_service import ConfigService


class Container():
    def __init__(self):
        punq_container = punq.Container()
        punq_container.register(ConfigService, instance=ConfigService())

        self.punq_container = punq_container

    def get_container(self):
        return self.punq_container
    


container = Container()


def get_config_service() -> ConfigService:
    return container.get_container().resolve(ConfigService) 