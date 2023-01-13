from logger.logging import service_logger
from harp_daemon.models.notifications import Notifications

log = service_logger()


def event_in_db(notification):
    get_notification = Notifications.get_notification(
        studio=notification['studio'],
        ms_alert_id=notification['ms_alert_id'],
        alert_name=notification['alert_name'],
        source=notification['source'],
        ms=notification['monitoring_system'],
        object_name=notification['object_name']
    )

    exist_notification = [single_notification.json() for single_notification in get_notification]

    if len(exist_notification) != 0:
        """Event present in notifications"""
        return exist_notification[0]
    else:
        """Event is new"""
        return {}


def check_if_alert_ok(notification):
    """
    Alert status:
    0 - OK
    1 - CRITICAL
    10 - Ack
    """
    exist_event = event_in_db(notification)

    if notification['notification_status'] == 0:
        if exist_event == {}:
            """Notification status is 0 and it`s not registered in system"""

            return 'to_ignore'
        elif exist_event['notification_status'] == 0:
            """Notification status is 0 and in DB status is 0"""

            return 'to_ignore'
        else:
            """Notification status is 0 and in DB status is NOT 0"""

            return 'to_process'
    elif notification['notification_status'] == 10:
        """Notification status is 10 - acknowledge"""

        return 'to_acknowledge'
    elif notification['notification_status'] in [1, 2, 3, 4, 5]:
        try:
            return 'to_process'
        except KeyError:
            return 'to_process'
    else:
        log.error(
            msg=f"Unknown notification_status: {notification['notification_status']}",
            extra={"tags": {"event_id": notification["event_id"]}}
        )
        raise Exception(f"Unknown notification_status: {notification['notification_status']}")
