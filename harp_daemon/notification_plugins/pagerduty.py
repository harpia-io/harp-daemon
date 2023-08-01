import ujson as json
from harp_daemon.models.active_alerts import ActiveAlerts
from logger.logging import service_logger
import harp_daemon.settings as settings
from harp_daemon.notification_processors.pagerduty_processor import GenerateAutoPagerduty
from harp_daemon.handlers.env_processor import env_id_to_name
from harp_daemon.models.notifications import Notifications
from harp_daemon.tools.prometheus_metrics import Prom
from harp_daemon.models.notification_history import NotificationHistory
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class PagerdutyHandler(object):
    def __init__(self, notification, action):
        self.notification = notification
        self.action = action
        self.recipient_id = None
        self.notification_type = 'pagerduty'

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

        if 'action_by' in self.notification:
            data['action_by'] = self.notification['action_by']

        return data

    @tracer.start_as_current_span("update_alerts_template")
    def update_alerts_template(self):
        data = {
            'severity': self.notification['severity'],
            'department': self.notification['exist_alert_body']['department'],
            'notification_status': self.notification['notification_status']
        }

        if 'snooze_expire_ts' in self.notification:
            data['snooze_expire_ts'] = self.notification['snooze_expire_ts']

        if 'action_by' in self.notification:
            data['action_by'] = self.notification['action_by']

        return data

    @tracer.start_as_current_span("define_rendered_image")
    def define_rendered_image(self):
        image = json.loads(self.notification['exist_alert_body']['image'])
        if image:
            return image

    @tracer.start_as_current_span("process_pagerduty")
    def process_pagerduty(self, action, api_key=None, recipient_id=None, description=None):
        if recipient_id is None:
            recipient_id = self.notification['exist_alert_body']['recipient_id']

        if api_key is None:
            pagerduty_routing_key = self.notification['procedure']['ids']
        else:
            pagerduty_routing_key = api_key

        process_event = GenerateAutoPagerduty(
            pagerduty_routing_key=pagerduty_routing_key,
            event_id=self.notification['event_id'],
            object_name=self.notification['exist_alert_body']['object_name'],
            service=self.notification['exist_alert_body']['service'],
            notification_output=json.loads(self.notification['exist_alert_body']['output']),
            alert_id=self.notification['exist_alert_body']['id'],
            alert_name=self.notification['exist_alert_body']['name'],
            graph_url=self.notification['graph_url'],
            additional_fields=json.loads(self.notification['exist_alert_body']['additional_fields']),
            description=description,
            studio=env_id_to_name(env_id=self.notification['exist_alert_body']['studio'])
        )

        if action == 'create_event':
            self.recipient_id = process_event.create_event(
                recipient_id=recipient_id
            )

        elif action == 'update_event':
            self.recipient_id = process_event.update_event(
                recipient_id=recipient_id
            )

        elif action == 'close_event':
            process_event.close_event(
                recipient_id=recipient_id
            )

        if self.recipient_id:
            Notifications.update_exist_event(data={'recipient_id': self.recipient_id}, event_id=self.notification['exist_alert_body']['id'])

        if recipient_id is not None:
            return self.recipient_id

    @Prom.PD_CREATE_NOTIFICATION.time()
    @tracer.start_as_current_span("create_event")
    def create_event(self):
        self.process_pagerduty(action='create_event')
        ActiveAlerts.add_new_event(data=self.active_alerts_template())

        NotificationHistory.update_alert_history(
            alert_id=self.notification['exist_alert_body']['id'],
            notification_output=f"PD routing_key: {', '.join(self.notification['procedure']['ids'])}",
            notification_action="Created PagerDuty event"
        )

    @Prom.PD_UPDATE_NOTIFICATION.time()
    @tracer.start_as_current_span("update_event")
    def update_event(self):
        self.process_pagerduty(action='update_event')
        ActiveAlerts.update_exist_event(data=self.update_alerts_template(), event_id=self.notification['exist_alert_body']['id'])

        NotificationHistory.update_alert_history(
            alert_id=self.notification['exist_alert_body']['id'],
            notification_output=f"PD routing_key: {', '.join(self.notification['procedure']['ids'])}",
            notification_action="Updated PagerDuty event"
        )

    @Prom.PD_CLOSE_NOTIFICATION.time()
    @tracer.start_as_current_span("close_event")
    def close_event(self):
        self.process_pagerduty(action='close_event')
        ActiveAlerts.delete_exist_event(event_id=self.notification['exist_alert_body']['id'])

        NotificationHistory.update_alert_history(
            alert_id=self.notification['exist_alert_body']['id'],
            notification_output=f"PD routing_key: {', '.join(self.notification['procedure']['ids'])}",
            notification_action="Closed PagerDuty event"
        )

    @tracer.start_as_current_span("track_statistics")
    def track_statistics(self):
        if settings.DEEP_REPORTING == "true":
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
        elif self.action == 'Change severity':
            self.update_event()
        elif self.action == 'Resubmit event':
            pass
        elif self.action == 'Update event':
            pass
        else:
            log.error(
                msg=f"Unknown event action: {self.action}, notification: {self.notification}",
                extra={"tags": {"event_id": self.notification["event_id"]}}
            )
