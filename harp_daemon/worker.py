from harp_daemon.handlers.notification_processor import NotificationDaemon
import harp_daemon.decorators as decorators
from logger.logging import service_logger
import harp_daemon.settings as settings

log = service_logger()


class ProcessNotification(object):
    def __init__(self, notification):
        self.notification = notification

    def main(self):
        if settings.IGNORE_ALL_MESSAGES == "true":
            return 'Ignored'

        check_if_alert_ok = decorators.check_if_alert_ok(self.notification)
        if check_if_alert_ok != 'to_ignore':
            event = NotificationDaemon(self.notification)
            event.process_alert(check_if_alert_ok)
