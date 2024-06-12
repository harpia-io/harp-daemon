import logging
import harp_daemon.settings as settings
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from fastapi.logger import logger as fastapi_logger
from opensearch_logger import OpenSearchHandler

logger = None


class MetricsEndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


class HealthEndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(f"GET /{settings.SERVICE_NAME}/api/v1/health") == -1


def fastapi_logging():
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger = logging.getLogger("gunicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_error_logger = logging.getLogger("uvicorn.error")

    if settings.RUNNING_ON == 'kubernetes':
        opensearch_handler = OpenSearchHandler(
            index_name=settings.SERVICE_NAME,
            hosts=["http://opensearch-ingest-hl.opensearch.svc.cluster.local:9200"],
            http_auth=("admin", "admin"),
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )

        formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s")

        opensearch_handler.setFormatter(formatter)
        uvicorn_error_logger.addHandler(opensearch_handler)
        gunicorn_logger.addHandler(opensearch_handler)
        gunicorn_error_logger.addHandler(opensearch_handler)
        uvicorn_access_logger.addHandler(opensearch_handler)
        fastapi_logger.addHandler(opensearch_handler)
    # Filter out /endpoint
    logging.getLogger("uvicorn.access").addFilter(MetricsEndpointFilter())
    logging.getLogger("uvicorn.access").addFilter(HealthEndpointFilter())


def service_logger():
    global logger
    if not logger:
        logger = logging.getLogger(settings.SERVICE_NAME)
        logger.setLevel(settings.LOG_LEVEL)
        LoggingInstrumentor().instrument(set_logging_format=True)
        formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s")

        if settings.RUNNING_ON == 'kubernetes':
            opensearch_handler = OpenSearchHandler(
                index_name=settings.SERVICE_NAME,
                hosts=["http://opensearch-ingest-hl.opensearch.svc.cluster.local:9200"],
                http_auth=("admin", "admin"),
                http_compress=True,
                use_ssl=False,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
            opensearch_handler.setFormatter(formatter)
            logger.addHandler(opensearch_handler)

    return logger
