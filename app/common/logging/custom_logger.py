from typing import Any, Optional


class ZanellaLoggerOptions:
    context: str
    message: Optional[str]
    exData: Optional[Any]
    request: Optional[Any]
    response: Optional[Any]
    exception: Optional[Exception]

    def __init__(
        self,
        context,
        message: str,
        exData: Any,
        request: Any,
        response: Any,
        exception: Exception
    ):
        self.context = context
        self.message = message
        self.exData = exData
        self.request = request
        self.response = response
        self.exception = exception
