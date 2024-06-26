from harp_daemon.models.active_alerts import ActiveAlerts
from logger.logging import service_logger
import harp_daemon.settings as settings
from harp_daemon.handlers.assign_processor import AssignProcessor
from harp_daemon.tools.prometheus_metrics import Prom
from harp_daemon.models.notification_history import NotificationHistory
import ujson as json
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class UIHandler(object):
    def __init__(self, notification, action):
        self.notification = notification
        self.action = action
        self.notification_type = 'ui'

    @tracer.start_as_current_span("define_notification_type")
    def define_notification_type(self):
        notification_type = settings.NOTIFICATION_TYPE_MAPPING[self.notification_type]

        return notification_type

    @tracer.start_as_current_span("active_alerts_template")
    def active_alerts_template(self):
        data = {
            'alert_id': self.notification['exist_alert_body']['id'],
            'alert_name': self.notification['exist_alert_body']['name'],
            'studio': self.notification['exist_alert_body']['studio'],
            'ms': self.notification['exist_alert_body']['ms'],
            'source': self.notification['exist_alert_body']['source'],
            'service': self.notification['exist_alert_body']['service'],
            'object_name': self.notification['exist_alert_body']['object_name'],
            'severity': self.notification['severity'],
            'department': self.notification['exist_alert_body']['department'],
            'ms_alert_id': self.notification['exist_alert_body']['ms_alert_id'],
            'notification_type': self.define_notification_type(),
            'notification_status': self.notification['notification_status'],
            'total_duration': self.notification['exist_alert_body']['total_duration'],
            'additional_fields': self.notification['exist_alert_body']['additional_fields']
        }

        if 'snooze_expire_ts' in self.notification:
            data['snooze_expire_ts'] = self.notification['snooze_expire_ts']

        if 'assign_status' in self.notification:
            data['assign_status'] = self.notification['assign_status']

        if 'action_by' in self.notification:
            data['action_by'] = self.notification['action_by']

        return data

    @tracer.start_as_current_span("update_alerts_template")
    def update_alerts_template(self):
        data = {
            'severity': self.notification['severity'],
            'additional_fields': json.dumps(self.notification['additional_fields']),
            'notification_status': self.notification['notification_status']
        }

        if 'snooze_expire_ts' in self.notification:
            data['snooze_expire_ts'] = self.notification['snooze_expire_ts']

        if 'assign_status' in self.notification:
            data['assign_status'] = self.notification['assign_status']

        if 'action_by' in self.notification:
            data['action_by'] = self.notification['action_by']

        return data

    @Prom.UI_CREATE_NOTIFICATION.time()
    @tracer.start_as_current_span("create_event")
    def create_event(self):
        ActiveAlerts.add_new_event(data=self.active_alerts_template())

        if self.notification['assign_status'] == 1:
            assign = AssignProcessor(notification=self.notification)
            assign.process_assign(notification_action='create_event')

        NotificationHistory.update_alert_history(
            alert_id=self.notification['exist_alert_body']['id'],
            notification_output=f"",
            notification_action="Created UI event"
        )

    @Prom.UI_UPDATE_NOTIFICATION.time()
    @tracer.start_as_current_span("update_event")
    def update_event(self):
        ActiveAlerts.update_exist_event(data=self.update_alerts_template(), event_id=self.notification['exist_alert_body']['id'])

        if self.notification['assign_status'] == 1:
            assign = AssignProcessor(notification=self.notification)
            assign.process_assign(notification_action='update_event')

    @Prom.UI_RESUBMIT_NOTIFICATION.time()
    @tracer.start_as_current_span("resubmit_event")
    def resubmit_event(self):
        ActiveAlerts.update_exist_event(data=self.update_alerts_template(), event_id=self.notification['exist_alert_body']['id'])

        if self.notification['assign_status'] == 1:
            assign = AssignProcessor(notification=self.notification)
            assign.process_assign(notification_action='still_exist')

        NotificationHistory.update_alert_history(
            alert_id=self.notification['exist_alert_body']['id'],
            notification_output=f"",
            notification_action="Resubmitted UI event"
        )

    @Prom.UI_CLOSE_NOTIFICATION.time()
    @tracer.start_as_current_span("close_event")
    def close_event(self):
        ActiveAlerts.delete_exist_event(event_id=self.notification['exist_alert_body']['id'])

        if self.notification['assign_status'] == 1:
            assign = AssignProcessor(notification=self.notification)
            assign.process_assign(notification_action='close_event')

        NotificationHistory.update_alert_history(
            alert_id=self.notification['exist_alert_body']['id'],
            notification_output=f"",
            notification_action="Closed UI Event"
        )

    @tracer.start_as_current_span("track_statistics")
    def track_statistics(self):
        if settings.DEEP_REPORTING == "true":
            if 'additional_fields' in self.notification:
                if self.notification['additional_fields']:
                    for label_name, label_value in self.notification['additional_fields'].items():
                        Prom.notification_statistics_by_labels.labels(
                            notification_action=self.action,
                            alert_name=self.notification['exist_alert_body']['name'],
                            ms=self.notification['exist_alert_body']['ms'],
                            source=self.notification['exist_alert_body']['source'],
                            object_name=self.notification['exist_alert_body']['object_name'],
                            notification_type=self.notification_type,
                            severity=settings.SEVERITY_MAPPING[self.notification['severity']],
                            label_name=label_name,
                            label_value=label_value
                        ).inc(1)

        Prom.notification_statistics_alert_duration.labels(
            notification_action=self.action,
            alert_name=self.notification['exist_alert_body']['name'],
            ms=self.notification['exist_alert_body']['ms'],
            source=self.notification['exist_alert_body']['source']
        ).set(int(self.notification['exist_alert_body']['total_duration']))

        Prom.notification_statistics_by_alert_name.labels(
            notification_action=self.action,
            alert_name=self.notification['exist_alert_body']['name'],
            ms=self.notification['exist_alert_body']['ms'],
            source=self.notification['exist_alert_body']['source'],
            object_name=self.notification['exist_alert_body']['object_name'],
            notification_type=self.notification_type,
            severity=settings.SEVERITY_MAPPING[self.notification['severity']],
            notification_status=settings.NOTIFICATION_STATUS_MAPPING[self.notification['notification_status']],
        ).inc(1)

    @tracer.start_as_current_span("process_alert")
    def process_alert(self):
        self.track_statistics()
        if self.action == 'Close event':
            self.close_event()
        elif self.action == 'Create event' or self.action == 'Reopen event':
            self.create_event()
        elif self.action == 'Update event' or self.action == 'Change severity':
            self.update_event()
        elif self.action == 'Resubmit event':
            self.resubmit_event()
        else:
            log.error(
                msg=f"Unknown event action: {self.action}, notification: {self.notification}",
                extra={"tags": {"event_id": self.notification["event_id"]}}
            )
