from logger.logging import service_logger
from datetime import datetime
import harp_daemon.settings as settings
import base64
from skpy import Skype
import time, os, stat
from skpy import SkypeAuthException
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class GenerateAutoSkype(object):
    def __init__(self, event_id, rendered_graph, notification_output, object_name, service, alert_name, alert_id, skype_id, description, studio, graph_url=None, additional_fields=None):
        self.skype_id = skype_id
        self.event_id = event_id
        self.rendered_graph = rendered_graph
        self.graph_url = graph_url
        self.notification_output = notification_output
        self.alert_id = alert_id
        self.object_name = object_name
        self.notification_output = notification_output
        self.service = service
        self.alert_name = alert_name
        self.additional_fields = additional_fields
        self.description = description
        self.studio = studio
        self.skype = None

    @tracer.start_as_current_span("init_skype_connection")
    def init_skype_connection(self):
        token = f'{settings.SKYPE_TEMP_FILES}/SkypeTokenFile'
        if os.path.exists(token):
            if self.file_age_in_seconds(token) > 82800:
                os.remove(token)

        try:
            self.skype = Skype(connect=False)
            self.skype.conn.setTokenFile(token)

            try:
                self.skype.conn.readToken()
            except SkypeAuthException:
                self.skype.conn.setUserPwd(settings.SKYPE_USER, settings.SKYPE_PASS)
                self.skype.conn.getSkypeToken()
        except Exception as err:
            log.error(
                msg=f"Can`t connect to Skype: {err}. Proxy: {os.environ['https_proxy'], os.environ['http_proxy']}",
                extra={"tags": {"event_id": self.event_id}}
            )

    @staticmethod
    @tracer.start_as_current_span("file_age_in_seconds")
    def file_age_in_seconds(pathname):
        return int(time.time() - os.stat(pathname)[stat.ST_MTIME])

    @tracer.start_as_current_span("define_subject_name")
    def define_subject_name(self):
        subject_name = f"{self.alert_name}"

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
            additional_fields_lst.append(f"<i><b>Description:</b> {self.description}</i>")

        if self.studio and self.studio != "Other":
            additional_fields_lst.append(f"<i><b>Studio:</b> {self.studio}</i>")

        if self.service and self.service != "Other":
            additional_fields_lst.append(f"<i><b>Service:</b> {self.service}</i>")

        if self.object_name:
            additional_fields_lst.append(f"<i><b>Host:</b> {self.object_name}</i>")

        if 'current' in self.notification_output:
            additional_fields_lst.append(f"<i><b>Current Alert Output:</b> {self.notification_output['current']}</i>")

        if 'previous' in self.notification_output:
            additional_fields_lst.append(f"<i><b>Previous Alert Output:</b> {self.notification_output['previous']}</i>")

        additional_fields_lst.append(f"<i><b>Link to Alert:</b> {self.define_harp_event_url()}</i>")

        for key, value in self.additional_fields.items():
            if key not in exclude_list and len(str(value)) > 1:
                additional_fields_lst.append("<i><b>{0}:</b> {1}</i>".format(key, value))

        return '\n'.join(additional_fields_lst)

    @tracer.start_as_current_span("prepare_create_message")
    def prepare_create_message(self, action):
        time_now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        if action == 'create' or action == 'update':
            msg = f"{time_now}\n<b>Alert has been triggered - {self.define_subject_name()}</b>" \
                f"\n{self._prepare_additional_fields()}"
        elif action == 'still_exist':
            msg = f"{time_now}\n<b>Alert is still exist - {self.define_subject_name()}</b>" \
                f"\n<i><b>Link to Alert:</b> {self.define_harp_event_url()}</i>"
        else:
            msg = f"{time_now}\n<b>Alert has been closed - {self.define_subject_name()}</b>" \
                f"\n{self._prepare_additional_fields()}"

        return msg

    @tracer.start_as_current_span("skype_processor")
    def skype_processor(self, action):
        try:
            for single_skype in self.skype_id:
                self.init_skype_connection()
                chat = self.skype.contacts[single_skype].chat
                chat.sendMsg(self.prepare_create_message(action), rich=True)

                if self.rendered_graph:
                    time_now = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f')
                    file_img = settings.SKYPE_TEMP_FILES + "/{0}.png".format(time_now)
                    decoded_image = base64.b64decode(self.rendered_graph['res_img'].split(",")[1])
                    with open(file_img, 'wb') as fp:
                        fp.write(decoded_image)
                        fp.close()
                    file_to_read = open(file_img, 'rb')
                    chat.sendFile(content=file_to_read, image=True, name='image')
                    os.remove(file_img)
                    file_to_read.close()

                # log.info(
                #     msg=f"Skype chat has been started: {self.skype_id}",
                #     extra={"tags": {"event_id": self.event_id}}
                # )
        except Exception as err:
            log.error(msg=f"Can`t send Skype message: {err}")

    @tracer.start_as_current_span("create_chat")
    def create_chat(self):
        if settings.SKYPE_ACTIVE == "false":
            return 'fake_recipient_id'

        self.skype_processor(action='create')

    @tracer.start_as_current_span("update_chat")
    def update_chat(self):
        if settings.SKYPE_ACTIVE == "false":
            return 'fake_recipient_id'

        self.skype_processor(action='update')

    @tracer.start_as_current_span("still_exist_chat")
    def still_exist_chat(self):
        if settings.SKYPE_ACTIVE == "false":
            return 'fake_recipient_id'

        self.skype_processor(action='still_exist')

    @tracer.start_as_current_span("close_chat_comment")
    def close_chat_comment(self):
        if settings.SKYPE_ACTIVE == "false":
            return 'fake_recipient_id'

        self.skype_processor(action='close')


class VerifySkype(object):
    def __init__(self, skype_id, action_type, alert_id):
        self.skype_id = skype_id
        self.skype = None
        self.action_type = action_type
        self.alert_id = alert_id

    @tracer.start_as_current_span("init_skype_connection")
    def init_skype_connection(self):
        token = f'{settings.SKYPE_TEMP_FILES}/SkypeTokenFile'

        if self.file_age_in_seconds(token) > 82800:
            os.remove(token)

        self.skype = Skype(
            settings.SKYPE_USER,
            settings.SKYPE_PASS,
            tokenFile=token
        )

    @tracer.start_as_current_span("define_harp_event_url")
    def define_harp_event_url(self):
        if settings.DOCKER_SERVER_IP:
            notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
        else:
            notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

        return notification_url

    @staticmethod
    @tracer.start_as_current_span("file_age_in_seconds")
    def file_age_in_seconds(pathname):
        return int(time.time() - os.stat(pathname)[stat.ST_MTIME])

    @tracer.start_as_current_span("notify_message")
    def notify_message(self):
        msg = f"This is the test message from Harp Event console"

        return msg

    @tracer.start_as_current_span("format_skype_id")
    def format_skype_id(self):
        if isinstance(self.skype_id, list):
            return ','.join(self.skype_id)
        else:
            return self.skype_id

    @tracer.start_as_current_span("verify_skype")
    def verify_skype(self):
        try:
            self.init_skype_connection()
            chat = self.skype.contacts[self.format_skype_id()].chat

            if self.action_type == 'assign':
                chat.sendMsg(self.notify_message())

            # log.info(
            #     msg=f"New Skype has been added to auto notifications: {self.skype_id}"
            # )
            return True
        except Exception as err:
            log.error(
                msg=f"Error during adding Skype channel: {err}"
            )
            return False
