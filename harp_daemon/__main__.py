from pytz import utc
import logging
import harp_daemon.settings as settings
from harp_daemon.api.endpoints import router as endpoints
from harp_daemon.api.health import router as health
from harp_daemon.api.consumer import router as consumer
from apscheduler.schedulers.background import BackgroundScheduler
from logger.logging import service_logger
from logger.logging import fastapi_logging
from harp_daemon.plugins.tracer import get_tracer
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware
from harp_daemon.scheduler.notification_scheduler import scheduler_processor
from harp_daemon.scheduler.assign_scheduler import assign_processor
from harp_daemon.scheduler.alert_resubmit_scheduler import alert_resubmit_processor

from fastapi import FastAPI, Request, status

log = service_logger()
fastapi_logging()
tracer = get_tracer()


app = FastAPI(
    openapi_url=f'{settings.URL_PREFIX}/openapi.json',
    docs_url=f'{settings.URL_PREFIX}/docs',
    redoc_url=f'{settings.URL_PREFIX}/redoc'
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.error(
        msg=f"FastAPI: Failed to validate request\nURL: {request.method} - {request.url}\nBody: {exc.body}\nError: {exc.errors()}"
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


def schedule_jobs():
    scheduler = BackgroundScheduler()
    scheduler.configure(timezone=utc)
    scheduler.start()
    scheduler.add_job(scheduler_processor, trigger='interval', seconds=10)
    scheduler.add_job(assign_processor, trigger='interval', seconds=30)
    scheduler.add_job(alert_resubmit_processor, trigger='interval', seconds=60)
    logging.getLogger(settings.SERVICE_NAME).setLevel(logging.WARNING)


origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# init_consumer()
FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
Instrumentator().instrument(app).expose(app)
app.include_router(health)
app.include_router(endpoints)
app.include_router(consumer)
schedule_jobs()
