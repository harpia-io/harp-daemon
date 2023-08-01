from logger.logging import service_logger
from jira import JIRA
from datetime import datetime
import os
import harp_daemon.settings as settings
import base64
import traceback
from harp_daemon.handlers.get_bot_config import bot_config
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class GenerateAutoJira(object):
    def __init__(self, event_id, rendered_graph, notification_output, object_name, service, alert_name, alert_id, project, description, studio, graph_url=None, additional_fields=None):
        self.project = project
        self.event_id = event_id
        self.rendered_graph = rendered_graph
        self.graph_url = graph_url
        self.notification_output = notification_output
        self.alert_id = alert_id
        self.object_name = object_name
        self.notification_output = notification_output
        self.service = service
        self.alert_name = alert_name
        self.description = description
        self.studio = studio
        self.jira = None
        self.additional_fields = additional_fields
        self.recipient_id = None
        self.bot_config = bot_config(bot_name='jira')

    @tracer.start_as_current_span("init_jira_connection")
    def init_jira_connection(self):
        os.environ['https_proxy'] = ''
        os.environ['http_proxy'] = ''
        self.jira = JIRA(
            options={'server': self.bot_config['JIRA_SERVER'], 'verify': False},
            basic_auth=(self.bot_config['JIRA_USER'], self.bot_config['JIRA_PASSWORD']),
            timeout=settings.JIRA_TIMEOUT
        )

    @tracer.start_as_current_span("define_subject_name")
    def define_subject_name(self):
        subject_name = f"[AUTO] {self.alert_name} - {self.object_name}"

        return subject_name

    @tracer.start_as_current_span("define_harp_event_url")
    def define_harp_event_url(self):
        if settings.DOCKER_SERVER_IP:
            notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
        else:
            notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

        return notification_url

    @tracer.start_as_current_span("_prepare_additional_fields")
    def _prepare_additional_fields(self):
        additional_fields_lst = []
        exclude_list = ["Action URL", "Note URL", "graph_url"]

        if self.description:
            additional_fields_lst.append(f"*Description*: {self.description}")

        if self.studio and self.studio != "Other":
            additional_fields_lst.append(f"*Studio*: {self.studio}")

        if self.service and self.service != "Other":
            additional_fields_lst.append(f"*Service*: {self.service}")

        if self.object_name:
            additional_fields_lst.append(f"*Host*: {self.object_name}")

        additional_fields_lst.append(f"*Alert Output*: {self.notification_output}")

        additional_fields_lst.append(f"*Link to Alert*: {self.define_harp_event_url()}")

        for key, value in self.additional_fields.items():
            if key not in exclude_list and len(str(value)) > 1:
                additional_fields_lst.append("*{0}*: {1}".format(key, value))

        return '\n'.join(additional_fields_lst)

    @tracer.start_as_current_span("_prepare_jira")
    def _prepare_jira(self):
        issue_dict = {
            'project': {'key': self.project},
            'summary': self.define_subject_name(),
            'description': self._prepare_additional_fields(),
            'issuetype': {'name': 'Task'}
        }

        if self.project.lower() == 'ite':
            issue_dict['customfield_31201'] = {"value": "1"}

        # log.info(
        #     msg=f"Prepare JIRA body: {issue_dict}",
        #     extra={"tags": {"event_id": self.event_id}}
        # )
        return issue_dict

    @tracer.start_as_current_span("_attache_graph")
    def _attache_graph(self, jira_key):
        time_now = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f')
        file_img = settings.JIRA_TEMP_FILES + "/{0}.png".format(time_now)

        if self.rendered_graph:
            # log.info(
            #     msg=f"Attache graph to JIRA",
            #     extra={"tags": {"event_id": self.event_id}}
            # )
            decoded_image = base64.b64decode(self.rendered_graph['res_img'].split(",")[1])
            with open(file_img, 'wb') as fp:
                fp.write(decoded_image)
            self.jira.add_attachment(issue=jira_key, attachment=file_img)
            os.remove(file_img)

    @tracer.start_as_current_span("get_issue_status")
    def get_issue_status(self, recipient_id):
        issue = self.jira.issue(id=recipient_id)

        issue_status = issue.fields.status

        return issue_status

    @tracer.start_as_current_span("create_jira")
    def create_jira(self, recipient_id):
        if settings.JIRA_ACTIVE == "false":
            return 'fake_recipient_id'

        if recipient_id:
            self.update_jira(recipient_id)
        else:
            self.init_jira_connection()
            jira_body = self._prepare_jira()
            self.recipient_id = self.jira.create_issue(fields=jira_body)
            self._attache_graph(jira_key=self.recipient_id)

            # log.info(
            #     msg=f"JIRA has been created: {self.recipient_id}",
            #     extra={"tags": {"event_id": self.event_id}}
            # )

        return str(self.recipient_id)

    @tracer.start_as_current_span("update_jira")
    def update_jira(self, recipient_id):
        if settings.JIRA_ACTIVE == "false":
            return 'fake_recipient_id'

        self.init_jira_connection()
        self.recipient_id = recipient_id
        issue_status = self.get_issue_status(recipient_id)
        log.info(msg=f"JIRA Status - {recipient_id}: {issue_status}", extra={"tags": {"event_id": self.event_id}})

        if str(issue_status) in ['Resolved', 'Done', 'Closed']:
            log.info(msg=f"JIRA was closed - {recipient_id}. Creating the new one", extra={"tags": {"event_id": self.event_id}})
            self.recipient_id = self.create_jira(recipient_id=None)
        else:
            add_comment = self.jira.add_comment(
                self.recipient_id,
                f'Problem repeated again:\n*Alert Output:* {self.notification_output}'
            )
            log.info(
                msg=f"JIRA has been updated: {add_comment}",
                extra={"tags": {"event_id": self.event_id}}
            )

        return str(self.recipient_id)

    @tracer.start_as_current_span("still_exist_jira")
    def still_exist_jira(self, recipient_id):
        if settings.JIRA_ACTIVE == "false":
            return 'fake_recipient_id'

        self.init_jira_connection()
        self.recipient_id = recipient_id
        add_comment = self.jira.add_comment(
            self.recipient_id,
            f'Issue is still exist'
        )

        log.info(
            msg=f"JIRA has been resubmitted: {add_comment}",
            extra={"tags": {"event_id": self.event_id}}
        )

        return str(self.recipient_id)

    @tracer.start_as_current_span("close_jira_comment")
    def close_jira_comment(self, recipient_id):
        if settings.JIRA_ACTIVE == "false":
            return 'fake_recipient_id'

        self.init_jira_connection()
        self.recipient_id = recipient_id
        add_comment = self.jira.add_comment(
            self.recipient_id, f'Alert has been resolved:\n*Alert Output:* {self.notification_output}'
        )
        log.info(
            msg=f"JIRA Comment has been closed: {add_comment}",
            extra={"tags": {"event_id": self.event_id}}
        )

        return self.recipient_id


class CreateJiraFromEvent(object):
    def __init__(self, notification_output, object_name, service, alert_name, alert_id, project, description, studio, author, graph_url=None, additional_fields=None):
        self.project = project
        self.graph_url = graph_url
        self.notification_output = notification_output
        self.alert_id = alert_id
        self.object_name = object_name
        self.notification_output = notification_output
        self.service = service
        self.alert_name = alert_name
        self.description = description
        self.studio = studio
        self.author = author
        self.jira = None
        self.additional_fields = additional_fields
        self.bot_config = bot_config(bot_name='jira')

    @tracer.start_as_current_span("init_jira_connection")
    def init_jira_connection(self):
        self.jira = JIRA(
            options={'server': self.bot_config['JIRA_SERVER'], 'verify': False},
            basic_auth=(self.bot_config['JIRA_USER'], self.bot_config['JIRA_PASSWORD']),
            timeout=settings.JIRA_TIMEOUT
        )

    @tracer.start_as_current_span("define_subject_name")
    def define_subject_name(self):
        subject_name = f"{self.alert_name} - {self.object_name}"

        return subject_name

    @tracer.start_as_current_span("define_harp_event_url")
    def define_harp_event_url(self):
        if settings.DOCKER_SERVER_IP:
            notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
        else:
            notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

        return notification_url

    @tracer.start_as_current_span("_prepare_additional_fields")
    def _prepare_additional_fields(self):
        additional_fields_lst = []
        exclude_list = ["Action URL", "Note URL", "graph_url"]

        if self.author:
            additional_fields_lst.append(f"*Author*: {self.author}")

        if self.description:
            additional_fields_lst.append(f"*Description*: {self.description}")

        if self.studio and self.studio != "Other":
            additional_fields_lst.append(f"*Studio*: {self.studio}")

        if self.service and self.service != "Other":
            additional_fields_lst.append(f"*Service*: {self.service}")

        if self.object_name:
            additional_fields_lst.append(f"*Host*: {self.object_name}")

        additional_fields_lst.append(f"*Alert Output*: {self.notification_output}")

        additional_fields_lst.append(f"*Link to Alert*: {self.define_harp_event_url()}")

        for key, value in self.additional_fields.items():
            if key not in exclude_list and len(str(value)) > 1:
                additional_fields_lst.append("*{0}*: {1}".format(key, value))

        return '\n'.join(additional_fields_lst)

    @tracer.start_as_current_span("_prepare_jira")
    def _prepare_jira(self):
        issue_dict = {
            'project': {'key': self.project},
            'summary': self.define_subject_name(),
            'description': self._prepare_additional_fields(),
            'issuetype': {'name': 'Task'}
        }

        if self.project.lower() == 'ite':
            issue_dict['customfield_31201'] = {"value": "1"}

        log.info(
            msg=f"Prepare JIRA body: {issue_dict}"
        )
        return issue_dict

    @tracer.start_as_current_span("create_jira")
    def create_jira(self,):
        self.init_jira_connection()
        jira_body = self._prepare_jira()
        recipient_id = self.jira.create_issue(fields=jira_body)

        log.info(
            msg=f"JIRA has been created: {recipient_id}"
        )

        return str(recipient_id)


class VerifyJIRA(object):
    def __init__(self, recipients, action_type, alert_id):
        self.recipients = recipients
        self.action_type = action_type
        self.alert_id = alert_id
        self.jira = None
        self.bot_config = bot_config(bot_name='jira')

    @tracer.start_as_current_span("init_jira_connection")
    def init_jira_connection(self):
        self.jira = JIRA(
            options={'server': self.bot_config['JIRA_SERVER'], 'verify': False},
            basic_auth=(self.bot_config['JIRA_USER'], self.bot_config['JIRA_PASSWORD']),
            timeout=settings.JIRA_TIMEOUT
        )

    @tracer.start_as_current_span("define_harp_event_url")
    def define_harp_event_url(self):
        if settings.DOCKER_SERVER_IP:
            notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
        else:
            notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

        return notification_url

    @tracer.start_as_current_span("jira_template")
    def jira_template(self):
        msg = f"This is the test JIRA from Harp Event console."

        return msg

    @tracer.start_as_current_span("verify_jira")
    def verify_jira(self):
        if self.action_type == 'assign':
            try:
                self.init_jira_connection()
                jira_number = self.recipients.split("/")[-1]
                add_comment = self.jira.add_comment(
                    jira_number,
                    self.jira_template()
                )

                log.info(
                    msg=f"Comment was added to JIRA: {add_comment}"
                )

                return True
            except Exception as err:
                log.error(f"Can`t assign to JIRA: {err}. Stack: {traceback.format_exc()}")
                return False
        else:
            return True
