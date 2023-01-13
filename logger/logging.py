import logging
import harp_daemon.settings as settings
import logging_loki
from multiprocessing import Queue
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from fastapi.logger import logger as fastapi_logger

logger = None


def fastapi_logging():
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger = logging.getLogger("gunicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_error_logger = logging.getLogger("uvicorn.error")

    loki_handler = logging_loki.LokiQueueHandler(
        Queue(-1),
        url=f"http://{settings.LOKI_SERVER}:{settings.LOKI_PORT}/loki/api/v1/push",
        tags={
            "service": settings.SERVICE_NAME,
            "namespace": settings.SERVICE_NAMESPACE
        },
        version="1",
    )
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d trace_id=%(otelTraceID)s span_id=%(otelSpanID)s - %(message)s')
    loki_handler.setFormatter(formatter)

    uvicorn_error_logger.addHandler(loki_handler)
    gunicorn_logger.addHandler(loki_handler)
    gunicorn_error_logger.addHandler(loki_handler)
    uvicorn_access_logger.addHandler(loki_handler)
    fastapi_logger.addHandler(loki_handler)


def service_logger():
    global logger
    if not logger:
        logger = logging.getLogger(settings.SERVICE_NAME)
        logger.setLevel(settings.LOG_LEVEL)

        loki_handler = logging_loki.LokiQueueHandler(
            Queue(-1),
            url=f"http://{settings.LOKI_SERVER}:{settings.LOKI_PORT}/loki/api/v1/push",
            tags={
                "service": settings.SERVICE_NAME,
                "namespace": settings.SERVICE_NAMESPACE,
            },
            version="1",
        )

        LoggingInstrumentor().instrument(set_logging_format=True)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d trace_id=%(otelTraceID)s span_id=%(otelSpanID)s - %(message)s')
        loki_handler.setFormatter(formatter)

        logger.addHandler(loki_handler)

    return logger
