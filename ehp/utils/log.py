import traceback
from typing import Any, Callable, Dict

import structlog
from elasticapm.handlers.structlog import structlog_processor
from structlog.processors import JSONRenderer

from ehp.settings import EnvTypes, Settings


class _LoggerType:
    msg: Callable
    info: Callable
    error: Callable
    warning: Callable
    exception: Callable


class LocalLogger:

    binds: Dict[str, Any]

    def __init__(self):
        self.binds = {}

    def bind(self, **kwargs):
        self.binds.update(kwargs)
        return self

    def msg(self, message: str, level: str, **kwargs):
        print()
        print(f"{level.upper()}:", self.binds["name"])
        if len(self.binds) > 1:
            print([(k, self.binds[k]) for k in self.binds if k != "name"])
        print(f"{message=}")
        print()
        for kwarg in kwargs:
            if kwarg == "__level":
                continue
            print(f"  -{kwarg}: {kwargs[kwarg]}")
        print()

    def info(self, message, **kwargs):
        self.msg(message, level="info", **kwargs)

    def warning(self, message, **kwargs):
        self.msg(message, level="warning", **kwargs)

    def exception(self, message, **kwargs):
        self.msg(message, level="exception", **kwargs)

    def error(self, message, **kwargs):
        self.msg(message, level="error", **kwargs)


def _event_to_message_processor(_, __, ed):
    ed["message"] = ed.pop("event")
    return ed


# ordering of processors is important
structlog.configure(
    processors=[_event_to_message_processor, structlog_processor, JSONRenderer()],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)


def get_logger(name: str, **kwargs) -> _LoggerType:

    if Settings.ENV == EnvTypes.DEV:
        logger = LocalLogger()
    else:
        logger = structlog.get_logger()
    logger = logger.bind(name=name, **kwargs)
    return logger


logger = get_logger(__name__)


def log_exception(logger_function: Callable, message: str, exception: Exception):
    if Settings.ENV in (EnvTypes.DEV, EnvTypes.TEST):
        print(f"{message=}")
        print(f"{exception=}")
        print(f"{traceback.format_exc()=}")
    else:
        logger_function(message, exc=str(exception), tb=traceback.format_exc())
