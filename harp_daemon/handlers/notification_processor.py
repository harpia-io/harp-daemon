from datetime import datetime
from logger.logging import service_logger
from harp_daemon.models.notifications import Notifications
from harp_daemon.models.assigne import Assign
import ujson as json
import harp_daemon.notification_plugins as handlers
import harp_daemon.decorators as decorators
from harp_daemon.models.notification_history import NotificationHistory
from harp_daemon.models.active_alerts import ActiveAlerts
import traceback
import harp_daemon.settings as settings
from harp_daemon.models.statistics import Statistics
from harp_daemon.handlers.period_processors import check_notification_period
from harp_daemon.notification_plugins.help_processors import check_licenses
from harp_daemon.plugins.kafka_confluent_producer import KafkaProduceMessages
from harp_daemon.handlers.scheduler_processors import Scheduler

producer = KafkaProduceMessages()

log = service_logger()


class NotificationDaemon(object):
    def __init__(self, notification, notification_action=None):
        self.notification = notification
        self.notification_type = None
        self.notification_action = notification_action
        self.new_event = False

    @staticmethod
    def transform_notification_type(notification_type):
        notification_type = settings.NOTIFICATION_TYPE_MAPPING[notification_type]

        log.debug(
            msg=f"transform_notification_type\n{notification_type}",
            extra={"tags": {}}
        )

        return notification_type

    def check_output_change(self) -> bool:
        """
        False: Current and previous output are the same
        True: Current and previous output different
        """

        event_output = json.loads(self.notification['exist_alert_body']['output'])

        if 'previous' in event_output:
            if event_output['previous'] == event_output['current']:
                log.debug(
                    msg=f"Output was not changed",
                    extra={"tags": {}}
                )

                return False
            else:
                log.debug(
                    msg=f"Output was changed",
                    extra={"tags": {}}
                )

                return True
        else:
            log.debug(
                msg=f"Previous output not found. Marked event output as not changed",
                extra={"tags": {}}
            )

            return False

    def get_assign_details(self):
        log.info(msg=f"AlertID to get assign info: {self.notification['exist_alert_body']['id']}")

        get_assign = Assign.get_assign_info(event_id=self.notification['exist_alert_body']['id'])

        log.info(msg=f"Get assign info: {get_assign}")

        exist_assign = [single_assign.json() for single_assign in get_assign][0]

        log.debug(
            msg=f"get_assign_details\n{exist_assign}",
            extra={"tags": {}}
        )

        return exist_assign

    def cancel_snooze_in_notification(self):
        """Snooze was reset to default in Notifications"""

        default_snooze_time = datetime(1970, 1, 1, 00, 00, 1)
        self.notification['snooze_expire_ts'] = default_snooze_time
        Notifications.update_exist_event(
            event_id=self.notification['exist_alert_body']['id'],
            data={"snooze_expire_ts": default_snooze_time}
        )

        log.debug(
            msg=f"Snooze was reset to default in Notifications",
            extra={"tags": {}}
        )

    def cancel_assign(self):
        """Assign status was reset to default in Notifications"""

        log.debug(
            msg=f"Assign status was reset to default in Notifications",
            extra={"tags": {}}
        )

        assign_status = 0
        self.notification['assign_status'] = assign_status
        Notifications.update_exist_event(
            event_id=self.notification['exist_alert_body']['id'],
            data={"assign_status": assign_status}
        )

        Assign.delete_assign(alert_id=self.notification['exist_alert_body']['id'])

    def check_notification_assign_status(self):
        """
        0 - cancel snooze
        2 - cancel snooze if output was changed
        3 - cancel snooze if severity was changed
        5 - don`t cancel snooze
        """
        self.notification['exist_assign'] = self.get_assign_details()

        if self.notification['exist_assign']['sticky'] == 0:
            if self.check_output_change():
                log.debug(
                    msg=f"Event without Sticky. Output was changed. Assign will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_assign()
            elif self.notification_action == "Reopen event" or self.notification_action == "Change severity":
                log.debug(
                    msg=f"Event without Sticky. Event was reopened. Assign will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_assign()
            else:
                log.debug(
                    msg=f"Event without Sticky. Event output and severity was not changed\n{self.notification}",
                    extra={"tags": {}}
                )

                self.notification['assign_status'] = self.notification['exist_alert_body']['assign_status']

        elif self.notification['exist_assign']['sticky'] == 2:
            if self.check_output_change():
                log.debug(
                    msg=f"Event without output Sticky and it was changed. Assign will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_assign()
            else:
                log.debug(
                    msg=f"Event without output Sticky but it was not changed\n{self.notification}",
                    extra={"tags": {}}
                )

                self.notification['assign_status'] = self.notification['exist_alert_body']['assign_status']

        elif self.notification['exist_assign']['sticky'] == 3:
            if self.check_severity_change():
                log.debug(
                    msg=f"Event without severity Sticky and severity was changed. Assign will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_assign()
            else:
                log.debug(
                    msg=f"Event without severity Sticky and it was not changed\n{self.notification}",
                    extra={"tags": {}}
                )

                self.notification['assign_status'] = self.notification['exist_alert_body']['assign_status']

        elif self.notification['exist_assign']['sticky'] == 5:
            log.debug(
                msg=f"Event with all Sticky\n{self.notification}",
                extra={"tags": {}}
            )

            self.notification['assign_status'] = self.notification['exist_alert_body']['assign_status']
        else:
            log.error(
                msg=f"Unknown sticky status: {self.notification['exist_alert_body']}",
                extra={"tags": {"event_id": self.notification["event_id"]}}
            )

    def check_notification_snooze_ts(self):
        """
        0 - cancel snooze
        2 - cancel snooze if output was changed
        3 - cancel snooze if severity was changed
        5 - don`t cancel snooze
        """
        if self.notification['exist_alert_body']['sticky'] == 0:
            if self.check_output_change():
                log.debug(
                    msg=f"Event without Sticky. Output was changed. Snooze will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_snooze_in_notification()
            elif self.notification_action == "Reopen event" or self.notification_action == "Change severity":
                log.debug(
                    msg=f"Event without Sticky. Event was reopened. Snooze will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_snooze_in_notification()
            else:
                log.debug(
                    msg=f"Event without Sticky. Event output and severity was not changed\n{self.notification}",
                    extra={"tags": {}}
                )

                self.notification['snooze_expire_ts'] = self.notification['exist_alert_body']['snooze_expire_ts']
                self.notification['action_by'] = self.notification['exist_alert_body']['action_by']
        elif self.notification['exist_alert_body']['sticky'] == 2:
            if self.check_output_change():
                log.debug(
                    msg=f"Event without output Sticky and it was changed. Snooze will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_snooze_in_notification()
            else:
                log.debug(
                    msg=f"Event without output Sticky but it was not changed\n{self.notification}",
                    extra={"tags": {}}
                )

                self.notification['snooze_expire_ts'] = self.notification['exist_alert_body']['snooze_expire_ts']
                self.notification['action_by'] = self.notification['exist_alert_body']['action_by']

        elif self.notification['exist_alert_body']['sticky'] == 3:
            if self.check_severity_change():
                log.debug(
                    msg=f"Event without severity Sticky and severity was changed. Snooze will be canceled\n{self.notification}",
                    extra={"tags": {}}
                )

                self.cancel_snooze_in_notification()
            else:
                log.debug(
                    msg=f"Event without severity Sticky and it was not changed\n{self.notification}",
                    extra={"tags": {}}
                )

                self.notification['snooze_expire_ts'] = self.notification['exist_alert_body']['snooze_expire_ts']
                self.notification['action_by'] = self.notification['exist_alert_body']['action_by']

        elif self.notification['exist_alert_body']['sticky'] == 5:
            log.debug(
                msg=f"Event with all Sticky\n{self.notification}",
                extra={"tags": {}}
            )

            self.notification['snooze_expire_ts'] = self.notification['exist_alert_body']['snooze_expire_ts']
            self.notification['action_by'] = self.notification['exist_alert_body']['action_by']
        else:
            log.error(
                msg=f"Unknown sticky status: {self.notification['exist_alert_body']}",
                extra={"event_id": self.notification['event_id'], "event_name": "check_alert_snooze_ts"}
            )

    def define_graph_time_range(self):
        if self.notification_type == 'email':
            graph_ranges = self.notification['procedure']['graph_ranges']
            if graph_ranges:
                return f"{graph_ranges[0]}h"

    def check_if_still_new(self):
        if self.new_event:
            log.debug(
                msg=f"Alert is new\n{self.new_event}",
                extra={"tags": {}}
            )
            return True

    def check_if_flapping(self):
        if settings.CHECK_ALERT_STATE_FLAPPING == "true":
            reopen_count = NotificationHistory.get_reopen_history(self.notification['exist_alert_body']['id'])

            if reopen_count > 5:
                log.debug(
                    msg=f"Alert is flapping",
                    extra={"tags": {}}
                )
                return True
            else:
                log.debug(
                    msg=f"Alert is not flapping",
                    extra={"tags": {}}
                )
                return False
        else:
            return False

    def check_if_urgent(self):
        if '[urgent]' in self.notification['alert_name'].lower():
            return True

    def check_if_test(self):
        if '[test]' in self.notification['alert_name'].lower():
            return True

    def define_notification_status(self):
        """
        0 - OK
        1 - Problem
        2 - New alert
        3 - flapping
        4 - Urgent
        5 - Test
        """
        if self.notification['notification_status'] == 0:
            return 0
        else:
            if self.check_if_test():
                self.notification['notification_status'] = 5
                return 5
            elif self.check_if_urgent():
                self.notification['notification_status'] = 4
                return 4
            elif self.check_if_still_new():
                self.notification['notification_status'] = 2
                return 2
            elif self.check_if_flapping():
                self.notification['notification_status'] = 3
                return 3
            else:
                self.notification['notification_status'] = 1
                return 1

    def define_notification_output(self):
        if self.notification['exist_alert_body'] == {}:
            notification_output = {
                'current': self.notification['notification_output']
            }
        else:
            notification_output = {
                'current': self.notification['notification_output'],
                'previous': json.loads(self.notification['exist_alert_body']['output'])['current']
            }

        return notification_output

    def filter_graphs(self):
        if self.notification['graph_url']:
            if 'grafana' in self.notification['graph_url']:
                if 'panelId' not in self.notification['graph_url'] and 'viewPanel' not in self.notification['graph_url']:
                    log.warning(
                        msg=f"incorrect Grafana url. It doesn't contain 'panelId' or 'viewPanel'. "
                            f"URL: {self.notification['graph_url']}",
                        extra={"tags": {"event_id": self.notification["event_id"]}}
                    )
                    return False
                else:
                    return True
            else:
                return True
        else:
            return True

    @staticmethod
    def define_image():
        # TODO: Enable Graph rendering
        return {}
        # if self.filter_graphs():
        #     try:
        #         event = GraphAPI(
        #             graph_url=self.notification['graph_url'],
        #             server=self.notification['source'],
        #             event_id=self.notification['event_id'],
        #             monitoring_system=self.notification['monitoring_system'],
        #             alert_name=self.notification['alert_name'],
        #             ms_unique_data=self.notification['ms_unique_data'],
        #             graph_time_range=self.define_graph_time_range()
        #         )
        #         result = event.get_graph()
        #         log.debug(
        #             msg=f"URL: {self.notification['graph_url']}. Graph render result: {result}",
        #             extra={"tags": {"event_id": self.notification["event_id"]}}
        #         )
        #         if result:
        #             result['res_img'] = 'data:image/png;base64,' + result['res_img']
        #
        #             return result
        #
        #     except Exception as err:
        #         log.debug(msg=f"can`t define_image: {err}. URL: {self.notification['graph_url']}")
        #         return {}
        # else:
        #     return {}

    def define_total_duration(self):
        if self.notification_action == 'Close event':
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            then = self.notification['exist_alert_body']['last_create_ts']
            fmt = '%Y-%m-%d %H:%M:%S'
            time1 = datetime.strptime(str(then), fmt)
            time2 = datetime.strptime(str(now), fmt)
            rev = time1 < time2
            difference = time2 - time1 if rev else time1 - time2
            total_duration = difference.seconds
        else:
            total_duration = self.notification['exist_alert_body']['total_duration']

        return int(total_duration)

    def new_notification_template(self):
        data = {
            'name': self.notification['alert_name'],
            'ms': self.notification['monitoring_system'],
            'studio': self.notification['studio'],
            'source': self.notification['source'],
            'object_name': self.notification['object_name'],
            'service': self.notification['service'],
            'severity': self.notification['severity'],
            'output': json.dumps(self.define_notification_output()),
            'additional_fields': json.dumps(self.notification['additional_fields']),
            'additional_urls': json.dumps(self.notification['additional_urls']),
            'actions': json.dumps(self.notification['actions']),
            'ms_alert_id': self.notification['ms_alert_id'],
            'notification_status': self.define_notification_status(),
            'procedure_id': self.notification['procedure_id'],
            'image': json.dumps(self.define_image())
        }

        return data

    def update_notification_template(self):
        data = {
            'severity': self.notification['severity'],
            'output': json.dumps(self.define_notification_output()),
            'additional_fields': json.dumps(self.notification['additional_fields']),
            'additional_urls': json.dumps(self.notification['additional_urls']),
            'actions': json.dumps(self.notification['actions']),
            'notification_status': self.define_notification_status(),
            'image': json.dumps(self.define_image()),
            'total_duration': self.define_total_duration(),
            'procedure_id': self.notification['procedure_id']
        }

        return data

    def update_last_update_ts(self):
        """
        Update time when event started
        """
        if self.notification_action == 'Reopen event':
            current_time = {"last_create_ts": datetime.utcnow()}

            return current_time

    def notification_operations(self, operation):
        if operation == 'add_new_notification':
            try:
                self.notification['exist_alert_body'] = Notifications.add_new_event(data=self.new_notification_template())
                log.info(
                    msg=f"Registered new alert\n Output: {self.notification['exist_alert_body']}",
                    extra={"tags": {"event_id": self.notification["event_id"]}}
                )
            except Exception as err:
                log.warn(msg=f"Cannot add new event - {err}")

        elif operation == 'update_exist_event':
            if self.update_last_update_ts():
                self.update_notification_template().update(self.update_last_update_ts())

            Notifications.update_exist_event(
                event_id=self.notification['exist_alert_body']['id'],
                data=self.update_notification_template()
            )

            get_notification = Notifications.get_notification_by_id(event_id=self.notification['exist_alert_body']['id'])
            exist_notification = [single_notification.json() for single_notification in get_notification][0]

            self.notification['exist_alert_body'] = exist_notification

    def check_severity_change(self):
        try:
            if self.notification['exist_alert_body']['severity'] == self.notification['severity']:
                return False
            else:
                """Severity was different"""

                return True
        except Exception:
            log.error(
                msg=f"Can`t check alert severity - {self.notification}\n Stack: {traceback.format_exc()}",
                extra={"tags": {"event_id": self.notification["event_id"]}}
            )
            raise Exception(f"Can`t check alert severity - {self.notification}\n")

    def check_alert_severity(self):
        get_exist_alert = ActiveAlerts.get_active_event_by_id(event_id=self.notification['exist_alert_body']['id'])
        exist_alert = [single_notification.json() for single_notification in get_exist_alert]

        try:
            if self.notification['exist_alert_body']['severity'] == self.notification['severity']:

                return False
            else:
                """Severity was different"""

                if exist_alert:
                    if exist_alert[0]['acknowledged'] == 1:
                        """Event in active_alerts marked as ACK. Going to remove this mark"""
                        ActiveAlerts.update_exist_event(event_id=self.notification['exist_alert_body']['id'], data={"acknowledged": 0})

                return True
        except Exception:
            log.error(
                msg=f"Can`t check alert severity - {self.notification}\n Stack: {traceback.format_exc()}",
                extra={"tags": {"event_id": self.notification["event_id"]}}
            )
            raise Exception(f"Can`t check alert severity - {self.notification}\n")

    @staticmethod
    def notification_statistics(notification_action, alert_id):
        get_counter = Statistics.get_counter(
            alert_id=alert_id,
        )

        exist_counters = [single_event.json() for single_event in get_counter]

        if len(exist_counters) == 0:
            """Event is new"""
            statistics = {
                "alert_id": alert_id,
                "create": 1
            }
            Statistics.add_new_event(data=statistics)
        elif notification_action == "Close event":
            Statistics.update_counter(
                alert_id=alert_id,
                data={
                    "close": exist_counters[0]['close'] + 1
                }
            )
        elif notification_action == "Reopen event":
            Statistics.update_counter(
                alert_id=alert_id,
                data={
                    "reopen": exist_counters[0]['reopen'] + 1
                }
            )
        elif notification_action == "Update event":
            Statistics.update_counter(
                alert_id=alert_id,
                data={
                    "update": exist_counters[0]['update'] + 1
                }
            )
        elif notification_action == "Change severity":
            Statistics.update_counter(
                alert_id=alert_id,
                data={
                    "change_severity": exist_counters[0]['change_severity'] + 1
                }
            )
        else:
            log.error(msg=f"Unknown statistics state - {notification_action}")

    def update_notification(self, notification_status):
        if notification_status == 'new':
            """Add NEW event to db and add 'exist_alert_body' to main notification"""

            self.notification_action = 'Create event'
            self.notification_operations(operation='add_new_notification')

        if notification_status == 'exist':
            if self.notification['notification_status'] == 0:
                """Current notification status is {self.notification['notification_status']}. Event will be closed"""

                self.notification_action = 'Close event'
            else:
                if self.notification['exist_alert_body']['notification_status'] in [1, 2, 3, 4, 5]:
                    if self.notification_action is None:
                        if self.check_alert_severity():
                            self.notification_action = 'Change severity'
                        else:
                            """Event will be updated"""
                            self.notification_action = 'Update event'
                else:
                    """Event will be reopened"""
                    self.notification_action = 'Reopen event'

            self.notification_operations(operation='update_exist_event')

        try:
            if self.notification_action != 'Update event':
                NotificationHistory.update_alert_history(
                    alert_id=self.notification['exist_alert_body']['id'],
                    notification_output=self.notification['notification_output'],
                    notification_action=self.notification_action
                )
        except Exception as err:
            log.error(
                msg=f"Can`t Update Alert History\nStack: {traceback.format_exc()}\nnotification_action: {self.notification_action}\n Error: {err}\n notification - {self.notification}",
                extra={"tags": {"event_id": self.notification["event_id"]}}
            )

        try:
            self.notification_statistics(
                notification_action=self.notification_action,
                alert_id=self.notification['exist_alert_body']['id']
            )
        except IndexError as err:
            log.error(
                msg=f"Can`t Update notifications statistics in DB for notification\nStack: {traceback.format_exc()}\nnotification_action: {self.notification_action}\n Error: {err}\n notification - {self.notification}",
                extra={"tags": {"event_id": self.notification["event_id"]}}
            )

    def check_notification_availability(self):
        if self.notification['exist_alert_body']:
            """Event was register in 'notification'"""

            self.update_notification(notification_status='exist')
        else:
            """Event is NEW"""

            self.new_event = True
            self.update_notification(notification_status='new')

    @staticmethod
    def push_message_to_kafka(topic, body, action):
        message = {
            "body": body,
            "action": action
        }
        producer.produce_message(
            topic=topic,
            message=message
        )

    @staticmethod
    def event_handler(notification_type, notification_action, notification_body):
        if notification_type == 'ui':
            event = handlers.UIHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'jira':
            event = handlers.JiraHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'email':
            event = handlers.EmailHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'skype':
            event = handlers.SkypeHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'telegram':
            event = handlers.TelegramHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'teams':
            event = handlers.TeamsHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'pagerduty':
            event = handlers.PagerdutyHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'sms':
            event = handlers.SMSHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'voice':
            event = handlers.VoiceHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'signl4':
            event = handlers.Signl4Handler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'slack':
            event = handlers.SlackHandler(notification=notification_body, action=notification_action)
            event.process_alert()

        if notification_type == 'webhook':
            event = handlers.WebhookHandler(notification=notification_body, action=notification_action)
            event.process_alert()

    def add_exist_event(self):
        event = decorators.ExistEvent(notification=self.notification)

        return event.add_exist_event()

    def process_event(self):
        for scenario in self.notification['procedure']['scenario_actions']:
            self.notification['procedure'] = scenario['body']
            self.notification_type = scenario['type']
            if check_notification_period(notification=self.notification) is not True:
                continue

            scheduler = Scheduler(
                alert_id=self.notification['exist_alert_body']['id'],
                scenario_type=scenario['type'],
                action=self.notification_action,
                scenario_body=scenario['body'],
                scenario_id=self.notification['procedure_id'],
                action_trigger_delay=scenario['action_trigger_delay']
            )

            if scheduler.main() is not True:
                continue

            # Check licenses
            if self.notification_action == 'Close event' or self.notification_action == 'Update event' or self.notification_action == 'Change severity':
                self.event_handler(
                    notification_action=self.notification_action,
                    notification_type=self.notification_type,
                    notification_body=self.notification
                )
            else:
                license_available = check_licenses(
                    notification_type=settings.NOTIFICATION_TYPE_MAPPING[self.notification_type],
                    event_id=self.notification['event_id']
                )
                if license_available:
                    self.event_handler(
                        notification_action=self.notification_action,
                        notification_type=self.notification_type,
                        notification_body=self.notification
                    )

    def process_alert(self, check_if_alert_ok):
        self.notification['exist_alert_body'] = self.add_exist_event()

        if check_if_alert_ok == 'to_process':
            self.check_notification_availability()
            if self.notification['exist_alert_body']['snooze_expire_ts'] != datetime(1970, 1, 1, 00, 00, 1):
                self.check_notification_snooze_ts()

            if self.notification['exist_alert_body']['assign_status'] == 1:
                self.check_notification_assign_status()
            else:
                self.notification['assign_status'] = 0

            if self.notification['procedure'] is not None:
                self.process_event()
            else:
                log.error(msg=f"Procedure ID is None\n{self.notification}")

        elif check_if_alert_ok == 'to_acknowledge':
            pass
