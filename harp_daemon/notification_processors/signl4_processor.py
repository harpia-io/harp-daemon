from logger.logging import service_logger
import harp_daemon.settings as settings
import requests
import json
import traceback
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class GenerateAutoSignl4(object):
	def __init__(self, signl4_webhook: list, notification_output, alert_name, alert_id, source, graph_url=None, additional_fields=None, additional_urls=None):
		self.signl4_webhook = signl4_webhook
		self.notification_output = notification_output
		self.alert_id = alert_id
		self.alert_name = alert_name
		self.source = source
		self.graph_url = graph_url
		self.additional_fields = additional_fields
		self.additional_urls = additional_urls

	@tracer.start_as_current_span("define_subject_name")
	def define_subject_name(self):
		subject_name = self.alert_name

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
		additional_fields_lst = {}

		if self.additional_fields is not None:
			for key, value in self.additional_fields.items():
				additional_fields_lst[key] = value

		return additional_fields_lst

	@tracer.start_as_current_span("prepare_additional_urls")
	def prepare_additional_urls(self):
		additional_urls_lst = {}

		if self.additional_urls is not None:
			for key, value in self.additional_urls.items():
				additional_urls_lst[key] = value

		return additional_urls_lst

	@tracer.start_as_current_span("create_message")
	def create_message(self, action):
		if action == 'create' or action == 'update':
			status = 'new'
		elif action == 'close':
			status = 'resolved'
		else:
			status = 'resolved'

		event_body = {
			"Id": str(self.alert_id),
			"Title": self.define_subject_name(),
			"Message": self.notification_output['current'],
			"Source": self.source,
			"X-S4-ExternalID": str(self.alert_id),
			"X-S4-Status": status,
			"X-S4-SourceSystem": "Harpia"
		}

		message = {**event_body, **self.prepare_additional_urls(), **self._prepare_additional_fields()}

		return message

	@tracer.start_as_current_span("signl4_processor")
	def signl4_processor(self, action):
		action_status = None
		for webhook in self.signl4_webhook:
			prepare_notification = self.create_message(action)

			try:
				req = requests.post(
					url=webhook,
					data=json.dumps(prepare_notification),
					headers={"Content-Type": "application/json"},
					timeout=30
				)

				if req.status_code not in [200, 201]:
					log.error(
						msg=f"Error: Can`t push notification to Signl4. Signl4 return status code {req.status_code}\nURL: {webhook}\ndata: {prepare_notification}"
					)
				else:
					action_status = req.json()
			except Exception as err:
				log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}")

		return action_status

	@tracer.start_as_current_span("create_alert")
	def create_alert(self):
		if settings.SIGNL4_ACTIVE == "false":
			return 'fake_recipient_id'

		return self.signl4_processor(action='create')

	@tracer.start_as_current_span("update_alert")
	def update_alert(self):
		if settings.SIGNL4_ACTIVE == "false":
			return 'fake_recipient_id'

		self.signl4_processor(action='update')

	@tracer.start_as_current_span("still_exist_alert")
	def still_exist_alert(self):
		if settings.SIGNL4_ACTIVE == "false":
			return 'fake_recipient_id'

		self.signl4_processor(action='still_exist')

	@tracer.start_as_current_span("close_alert")
	def close_alert(self):
		if settings.SIGNL4_ACTIVE == "false":
			return 'fake_recipient_id'

		self.signl4_processor(action='close')


# auto_signl4 = GenerateAutoSignl4(
# 	alert_id=2000,
# 	alert_name='Test Alert Name - 2000',
# 	signl4_webhook=['https://connect.signl4.com/webhook/cdhn1ttywb'],
# 	notification_output={'current': 'Alert Output'},
# 	source='https://appdynamics.com/link/to/alert',
# 	additional_fields={'field_1': 'value_1', 'field_2': 'value_2'},
# 	additional_urls={'url_1': 'link_1', 'url_2': 'link_2'}
# )
#
# print(auto_signl4.create_alert())
