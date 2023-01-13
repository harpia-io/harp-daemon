from logger.logging import service_logger
from fastapi import APIRouter
import harp_daemon.settings as settings
from harp_daemon.plugins.kafka_consumer import ProcessMessage, AutoResolveMessage
from harp_daemon.handlers.reassign_notification_environment import ReassignNotification
import threading

log = service_logger()

router = APIRouter(prefix=settings.URL_PREFIX)


def process_message():
    kafka_process_message = ProcessMessage(kafka_topic=settings.COLLETOR_NOTIFICATIONS_TOPIC)
    kafka_process_message.start_consumer()


def auto_resolve():
    kafka_process_message = AutoResolveMessage(kafka_topic=settings.RESOLVE_NOTIFICATIONS_TOPIC)
    kafka_process_message.start_consumer()


def reassign_notification():
    kafka_process_message = ReassignNotification(kafka_topic=settings.ENV_DELETION_TOPIC)
    kafka_process_message.start_consumer()


@router.on_event("startup")
async def init_consumer():
    t1 = threading.Thread(target=process_message, name='process_message', daemon=True)
    t2 = threading.Thread(target=auto_resolve, name='auto_resolve', daemon=True)
    t3 = threading.Thread(target=reassign_notification, name='reassign_notification', daemon=True)
    t1.start()
    t2.start()
    t3.start()
