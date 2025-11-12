import logging

from app.common.logging.custom_logger import ZanellaLoggerOptions
import structlog

from app.services.di.container import get_config_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

_config_svc = get_config_service()


def get_log_level() -> int:
    # info | warn | debug | error
    log_level = logging.INFO
    configured_log_level = _config_svc.get().app.log_level

    if configured_log_level.lower() == "warn":
        log_level = logging.WARN
    elif configured_log_level.lower() == "debug":
        log_level = logging.DEBUG
    elif configured_log_level.lower() == "error":
        log_level = logging.ERROR

    return log_level


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_data_processor(events: dict) -> dict:
    log_data = events.pop("log_data", None)
    if log_data is not None and isinstance(log_data, ZanellaLoggerOptions):
        for attr in ["context", "message", "exData", "request", "response", "exception"]:
            value = getattr(log_data, attr, None)
            if value is not None:
                events[attr] = None

    return events


log_processors = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.JSONRenderer()
]

structlog.configure(
    processors=log_processors,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(get_log_level())
)

formatter = structlog.stdlib.ProcessorFormatter(
    processors=log_processors
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

for log in []:
    logger = logging.getLogger(log)
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(get_log_level())

logger = structlog.get_logger()