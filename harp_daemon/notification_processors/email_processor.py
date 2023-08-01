from logger.logging import service_logger
import harp_daemon.settings as settings
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ujson as json
import base64
from harp_daemon.handlers.get_bot_config import bot_config
from harp_daemon.templates.email_template import template
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class GenerateAutoEmail(object):
    def __init__(
            self,
            rendered_graph,
            event_id,
            monitoring_system,
            object_name,
            service,
            notification_output,
            alert_id,
            studio,
            alert_name,
            recipients,
            description,
            source,
            graph_url=None,
            additional_fields=None

    ):
        self.recipient_id = None
        self.graph_url = graph_url
        self.rendered_graph = rendered_graph
        self.event_id = event_id
        self.additional_fields = additional_fields
        self.monitoring_system = monitoring_system
        self.object_name = object_name
        self.service = service
        self.notification_output = json.dumps(notification_output)
        self.studio = studio
        self.alert_name = alert_name
        self.recipients = recipients
        self.alert_id = alert_id
        self.description = description
        self.source = source
        self.smtp = None
        self.range_count = 1
        self.email_status = None
        self.bot_config = bot_config(bot_name='email')

    @tracer.start_as_current_span("define_harp_event_url")
    def define_harp_event_url(self):
        if settings.DOCKER_SERVER_IP:
            notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
        else:
            notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

        return notification_url

    @tracer.start_as_current_span("define_send_to_list")
    def define_send_to_list(self):
        send_to_list = self.recipients

        return send_to_list

    @tracer.start_as_current_span("decorate_additional_fields")
    def decorate_additional_fields(self):
        if self.additional_fields:
            if self.monitoring_system == 'zabbix':
                if '#TAGS' in self.additional_fields['Description']:
                    del self.additional_fields['Description']
                if 'Expression' in self.additional_fields:
                    del self.additional_fields['Expression']

            elif self.monitoring_system == 'api':
                if 'script' in self.additional_fields:
                    del self.additional_fields['script']

    @staticmethod
    @tracer.start_as_current_span("escape")
    def escape(s):
        s = s.replace("<", " < ")
        s = s.replace(">", " > ")

        return s

    @tracer.start_as_current_span("format_notification_output")
    def format_notification_output(self):
        output_dict = json.loads(self.notification_output)
        if 'current' in output_dict:
            if output_dict['current'] == '':
                del output_dict['current']

        if 'previous' in output_dict:
            if output_dict['previous'] == '':
                del output_dict['previous']

        return json.dumps(output_dict)

    @tracer.start_as_current_span("decorate_alert_details")
    def decorate_alert_details(self):
        HTML = ''

        HTML += f'\n<tr><th class=row_style><b>Alert Status:</b></th><td class=row_style>{self.email_status}</td></tr>'

        if self.description:
            HTML += f'\n<tr><th class=row_style><b>Description:</b></th><td class=row_style>{self.description}</td></tr>'

        if self.studio and self.studio != "Other":
            HTML += f'\n<tr><th class=row_style><b>Studio:</b></th><td class=row_style>{self.studio}</td></tr>'

        if self.source:
            HTML += f'\n<tr><th class=row_style><b>Source:</b></th><td class=row_style>{self.source}</td></tr>'

        if self.service and self.service != "Other":
            HTML += f'\n<tr><th class=row_style><b>Service:</b></th><td class=row_style>{self.service}</td></tr>'

        if self.monitoring_system == 'zabbix':
            HTML += f'\n<tr><th class=row_style><b>Host:</b></th><td class=row_style>{self.object_name}</td></tr>'

        HTML += f'\n<tr><th class=row_style><b>Alert Output:</b></th><td class=row_style>{self.escape(self.format_notification_output())}</td></tr>'

        HTML += f'\n<tr><th class=row_style><b>Link to Alert:</b></th><td class=row_style><a href={self.define_harp_event_url()}>{self.define_harp_event_url()}</td></tr>'

        return HTML

    @tracer.start_as_current_span("email_template")
    def email_template(self):
        exclude_list = ["Action URL", "Note URL", "graph_url"]

        HTML = '<html><head><style type="text/css">'
        HTML += '\nbody {text-align: left; font-family: calibri, sans-serif, verdana; font-size: 10pt}'
        HTML += '\ntable {margin-left: auto; margin-right: auto; border-collapse: collapse;}'
        HTML += '\nth.row_style, td.row_style {border-bottom: 1px solid black; padding: 10px; text-align: left}'

        HTML += '\na:link {color: #0095bf; text-decoration: none;}'
        HTML += '\na:visited {color: #0095bf; text-decoration: none;}'
        HTML += '\na:hover {color: #0095bf; text-decoration: underline;}'
        HTML += '\na:active {color: #0095bf; text-decoration: underline;}'
        HTML += '\nth {font-family: calibri, sans-serif, verdana; font-size: 12pt; text-align:left; white-space: nowrap; color: #535353;}'
        HTML += '\nth.perfdata {background-color: #0095bf; color: #ffffff; margin-left: 7px; margin-top: 5px; margin-bottom: 5px; text-align:center;}'
        HTML += '\ntd {font-family: calibri, sans-serif, verdana; font-size: 12pt; text-align:left}'
        HTML += '\ntd.center {margin-left: 71px; margin-top: 51px; margin-bottom: 51px; text-align:center;}'
        HTML += '\ntd.UP {background-color: #44bb77; color: #ffffff; margin-left: 2px; margin-top: 50px; margin-bottom: 50px}'
        HTML += '\ntd.DOWN {background-color: #ff5566; color: #ffffff; margin-left: 2px;}'
        HTML += '\ntd.UNREACHABLE {background-color: #aa44ff; color: #ffffff; margin-left: 2px;}'
        HTML += '\n</style></head><body>'
        HTML += f'\n<table class=bottomBorder width={settings.GRAPH["width"]}>'
        HTML += '\n<tr><th colspan=6 class=perfdata>Alert Details</th></tr>'

        HTML += self.decorate_alert_details()

        if self.additional_fields:
            for key, value in self.additional_fields.items():
                if key not in exclude_list and len(str(value)) > 1:
                    if str(value).startswith('http'):
                        HTML += f'\n<tr><th class=row_style><b>{key}:</b></th><td class=row_style><a href={value}>{value}</a></td></tr>'
                    else:
                        HTML += f'\n<tr><th class=row_style><b>{key}:</b></th><td class=row_style>{value}</td></tr>'

        HTML += '\n</table><br>'

        if self.graph_url:
            HTML += f'\n<table width={settings.GRAPH["width"]}>'
            HTML += '\n<tr><td class="center"><a href="' + self.graph_url + '"><img src="' + f"cid:grafana_perfdata_{self.range_count}" + '"></a></td></tr>'
            HTML += '\n</table><br>'

        HTML += f'\n<table width={settings.GRAPH["width"]}>'
        HTML += f'\n<tr><td class="center">Generated by https://{settings.SERVICE_NAMESPACE}.harpia.io</td></tr>'
        HTML += '\n</table><br>'
        HTML += '\n</body></html>'

        html_body = template.replace("{email_body}", HTML)

        return html_body

    @tracer.start_as_current_span("define_subject_name")
    def define_subject_name(self):
        subject_name = f"Harp alert: {self.alert_name} - {self.object_name}"

        return subject_name

    @tracer.start_as_current_span("prepare_email")
    def prepare_email(self):
        msgroot = MIMEMultipart('related')
        msgroot['From'] = self.bot_config['EMAIL_USER']
        msgroot['To'] = ', '.join(self.recipients)
        msgroot['Subject'] = self.define_subject_name()

        if self.recipient_id:
            if self.email_status not in ['resolved', 'still_exist']:
                self.email_status = 'updated'

            msgroot["In-Reply-To"] = self.recipient_id
            msgroot["References"] = self.recipient_id
        else:
            if self.email_status not in ['resolved', 'still_exist']:
                self.email_status = 'new'

            self.recipient_id = email.utils.make_msgid()

            msgroot["Message-ID"] = self.recipient_id

        msgroot.preamble = 'This is a multi-part message in MIME format.'
        msgalternative = MIMEMultipart('alternative')
        msgroot.attach(msgalternative)

        if self.rendered_graph:
            try:
                # log.info(
                #     msg=f"Attaching Graph to Email. res_img: {self.rendered_graph['res_img']}\ngraph_url: {self.rendered_graph['img_url']}",
                #     extra={"tags": {"event_id": self.event_id}}
                # )
                decoded_image = base64.b64decode(self.rendered_graph['res_img'].split(",")[1])
                msgimage = MIMEImage(decoded_image)
                msgimage.add_header('Content-ID', f'<grafana_perfdata_{self.range_count}>')
                msgroot.attach(msgimage)
            except TypeError as err:
                log.warning(
                    msg=f"Can`t process graph in Email. Error: {err}. res_img: {self.rendered_graph['res_img']}\ngraph_url: {self.rendered_graph['img_url']}",
                    extra={"tags": {"event_id": self.event_id}}
                )

        msgtext = MIMEText(self.email_template(), 'html')

        msgalternative.attach(msgtext)

        return msgroot

    @tracer.start_as_current_span("smtp_connection")
    def smtp_connection(self):
        try:
            self.smtp = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            self.smtp.login(user=self.bot_config['EMAIL_USER'], password=self.bot_config['EMAIL_PASSWORD'])
            # log.info(
            #     msg=f"Connected to SMTP",
            #     extra={"tags": {"event_id": self.event_id}}
            # )
        except Exception as err:
            log.error(
                msg=f"Can`t connect to SMTP:{err}",
                extra={"tags": {"event_id": self.event_id}}
            )

    @tracer.start_as_current_span("create_email")
    def create_email(self, recipient_id=None, email_status=None):
        """
        If recipient_id - update exist thread
        If absent create new thread and recipient_id
        """
        if settings.SMTP_ACTIVE == "false":
            return 'fake_recipient_id'

        self.email_status = email_status
        self.smtp_connection()
        self.recipient_id = recipient_id
        try:
            msgroot = self.prepare_email()
            # log.debug(
            #     msg=f""
            #     f"FROM: {self.bot_config['EMAIL_USER']}\n"
            #     f"define_send_to_list: {self.define_send_to_list()}\n"
            #     f"msgroot.as_string: {msgroot.as_string()}",
            #     extra={"tags": {"event_id": self.event_id}}
            # )

            self.smtp.sendmail(self.bot_config['EMAIL_USER'], self.define_send_to_list(), msgroot.as_string())
            self.smtp.close()

        except (smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused) as err:
            log.error(
                msg=f"Can`t send email: {err}",
                extra={"tags": {"event_id": self.event_id}}
            )

        return self.recipient_id

    @tracer.start_as_current_span("close_email")
    def close_email(self, recipient_id):
        if settings.SMTP_ACTIVE == "false":
            return 'fake_recipient_id'

        self.smtp_connection()
        self.recipient_id = recipient_id
        try:
            self.email_status = 'resolved'
            msgroot = self.prepare_email()
            # log.debug(
            #     msg=f""
            #     f"FROM: {self.bot_config['EMAIL_USER']}\n"
            #     f"define_send_to_list: {self.define_send_to_list()}\n"
            #     f"msgroot.as_string: {msgroot.as_string()}",
            #     extra={"tags": {"event_id": self.event_id}}
            # )
            self.smtp.sendmail(self.bot_config['EMAIL_USER'], self.define_send_to_list(), msgroot.as_string())
            self.smtp.close()
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused) as err:
            log.error(
                msg=f"Can`t send email: {err}",
                extra={"tags": {"event_id": self.event_id}}
            )

        return self.recipient_id


class VerifyEmail(object):
    def __init__(self, recipients, action_type, alert_id):
        self.recipients = recipients
        self.action_type = action_type
        self.alert_id = alert_id
        self.smtp = None
        self.bot_config = bot_config(bot_name='email')

    @tracer.start_as_current_span("smtp_connection")
    def smtp_connection(self):
        try:
            self.smtp = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            self.smtp.login(user=self.bot_config['EMAIL_USER'], password=self.bot_config['EMAIL_PASSWORD'])
            log.info(msg=f"Connected to SMTP")
        except Exception as err:
            log.error(msg=f"Can`t connect to SMTP:{err}")

    @tracer.start_as_current_span("define_harp_event_url")
    def define_harp_event_url(self):
        if settings.DOCKER_SERVER_IP:
            notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
        else:
            notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

        return notification_url

    @staticmethod
    @tracer.start_as_current_span("define_subject_name")
    def define_subject_name():
        msg = "Specific alert has been assigned to you"

        return msg

    @staticmethod
    @tracer.start_as_current_span("test_template")
    def test_template():
        msg = f"This is the test notification from Harp Event console"

        return msg

    @staticmethod
    @tracer.start_as_current_span("verify_template")
    def verify_template():
        msg = f"Your Email address was added to Harp Event console.\n" \
              f"You can start receiving notifications in case of the alert"

    @tracer.start_as_current_span("prepare_email")
    def prepare_email(self, msg):
        msgroot = MIMEMultipart('related')
        msgroot['From'] = self.bot_config['EMAIL_USER']
        msgroot['To'] = ', '.join(self.recipients)
        msgroot['Subject'] = self.define_subject_name()

        recipient_id = email.utils.make_msgid()

        msgroot["Message-ID"] = recipient_id

        msgroot.preamble = 'This is a multi-part message in MIME format.'
        msgalternative = MIMEMultipart('alternative')
        msgroot.attach(msgalternative)

        msgtext = MIMEText(msg, 'text')

        msgalternative.attach(msgtext)

        return msgroot

    @tracer.start_as_current_span("define_send_to_list")
    def define_send_to_list(self):
        send_to_list = self.recipients

        return send_to_list

    @tracer.start_as_current_span("verify_email")
    def verify_email(self):
        self.smtp_connection()
        try:
            if self.action_type == 'assign':
                msgroot = self.prepare_email(msg=self.verify_template())
            elif self.action_type == 'test':
                msgroot = self.prepare_email(msg=self.test_template())
            else:
                return True

            self.smtp.sendmail(self.bot_config['EMAIL_USER'], self.define_send_to_list(), msgroot.as_string())
            self.smtp.close()

            return True
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPSenderRefused) as err:
            log.error(
                msg=f"Can`t send email: {err}"
            )

            return False
