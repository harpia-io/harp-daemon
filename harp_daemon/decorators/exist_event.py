from harp_daemon.models.notifications import Notifications
from logger.logging import service_logger
from harp_daemon.models.active_alerts import ActiveAlerts


log = service_logger()


class ExistEvent(object):
    def __init__(self, notification):
        self.notification = notification

    def get_current_notification(self):
        """Check if event was registered previously"""

        get_notification = Notifications.get_notification(
            studio=self.notification['studio'],
            ms_alert_id=self.notification['ms_alert_id'],
            alert_name=self.notification['alert_name'],
            source=self.notification['source'],
            ms=self.notification['monitoring_system'],
            object_name=self.notification['object_name']
        )

        exist_notification = [single_notification.json() for single_notification in get_notification]

        if len(exist_notification) == 1:
            """Event present in notifications"""
            return exist_notification[0]
        elif len(exist_notification) == 0:
            """Event is new"""
            return {}
        else:
            """More than 1 notifications were found"""

            log.error(msg=f"More than 1 notification were found in Notifications table - {exist_notification}")

            return None

    def add_exist_event(self):
        return self.get_current_notification()
