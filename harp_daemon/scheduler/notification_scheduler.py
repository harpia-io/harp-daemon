from logger.logging import service_logger
from harp_daemon.handlers.notification_processor import NotificationDaemon
from harp_daemon.models.notification_scheduler import NotificationScheduler
from harp_daemon.models.notifications import Notifications
from harp_daemon.tools.prometheus_metrics import Prom
import harp_daemon.settings as settings
import requests
import traceback

log = service_logger()


class NotificationSchedulerChecker(object):
    @classmethod
    def get_scenario_by_id(cls, scenario_id):
        url = f"{settings.SCENARIOS_HOST}/{int(scenario_id)}"
        try:
            req = requests.get(
                url=url,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=10
            )
            if req.status_code == 200:
                return req.json()['msg']
            elif req.status_code == 404:
                return None
            else:
                log.error(
                    msg=f"Can`t connect to Scenario service to get Scenario by ID - {int(scenario_id)}\nStatus code: {req.status_code}\nJSON: {req.json()}"
                )
                return None
        except Exception as err:
            log.error(
                msg=f"Error: {err}, stack: {traceback.format_exc()}"
            )
            return None

    @staticmethod
    def get_scheduled_events():
        events_to_process = NotificationScheduler.get_events_to_process()

        return events_to_process

    @classmethod
    def get_recipients(cls, single_notification):
        scenario_id = single_notification['scenario_id']
        channel = single_notification['channel']

        get_scenario = cls.get_scenario_by_id(scenario_id)

        for single_action in get_scenario['scenario_actions']:
            if single_action['type'] == channel:
                if 'ids' in single_action['body']:
                    return single_action['body']['ids']
                else:
                    return single_action['body']['recipients']

    @staticmethod
    def delete_event(alert_id):
        NotificationScheduler.delete_exist_event(alert_id=alert_id)

    @classmethod
    def get_notification_body(cls, single_notification):
        notification_body = {}
        notification = Notifications.get_notification_by_id(event_id=single_notification['alert_id'])

        notification_body['exist_alert_body'] = [single_event.json() for single_event in notification][0]
        notification_body['notification_status'] = notification_body['exist_alert_body']['notification_status']
        notification_body['severity'] = notification_body['exist_alert_body']['severity']
        notification_body['snooze_expire_ts'] = notification_body['exist_alert_body']['snooze_expire_ts']
        notification_body['assign_status'] = notification_body['exist_alert_body']['assign_status']
        notification_body['procedure'] = {'recipients': cls.get_recipients(single_notification)}
        notification_body['procedure'] = {'ids': cls.get_recipients(single_notification)}
        notification_body['event_id'] = None
        notification_body['graph_url'] = None

        return notification_body

    @classmethod
    def process_scheduled_events(cls):
        for single_notification in cls.get_scheduled_events():
            try:
                NotificationDaemon.event_handler(
                    notification_action=single_notification['action'],
                    notification_body=cls.get_notification_body(single_notification=single_notification),
                    notification_type=single_notification['channel']
                )
                cls.delete_event(alert_id=single_notification['alert_id'])
            except Exception as err:
                log.error(msg=f"Cannot handle scheduled event - {single_notification}\nERROR: {err}\nTrace: {traceback.format_exc()}")


@Prom.NOTIFICATION_SCHEDULER_PROCESSOR.time()
def scheduler_processor():
    event = NotificationSchedulerChecker.process_scheduled_events()
