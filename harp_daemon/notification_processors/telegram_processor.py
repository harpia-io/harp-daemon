from logger.logging import service_logger
from datetime import datetime
import harp_daemon.settings as settings
import base64
from io import BytesIO
import requests
import json
import traceback

log = service_logger()
bio = BytesIO()


class GenerateAutoTelegram(object):
	def __init__(self, event_id, rendered_graph, notification_output, object_name, service, alert_name, alert_id, telegram_id, description, studio, graph_url=None, additional_fields=None):
		self.telegram_id = telegram_id
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
		self.bot = None

	def define_subject_name(self):
		subject_name = f"{self.alert_name}"

		return subject_name

	def define_harp_event_url(self):
		if settings.DOCKER_SERVER_IP:
			notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
		else:
			notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

		return notification_url

	def prepare_additional_fields(self):
		additional_fields_dict = {}
		exclude_list = ["Action URL", "Note URL", "graph_url"]

		if self.description:
			additional_fields_dict['Description'] = self.description

		if self.studio and self.studio != "Other":
			additional_fields_dict['Studio'] = self.studio

		if self.service and self.service != "Other":
			additional_fields_dict['Service'] = self.service

		if self.object_name:
			additional_fields_dict['Host'] = self.object_name

		if 'current' in self.notification_output:
			additional_fields_dict['Current Alert Output'] = self.notification_output['current']

		if 'previous' in self.notification_output:
			additional_fields_dict['Previous Alert Output'] = self.notification_output['previous']

		for key, value in self.additional_fields.items():
			if key not in exclude_list and len(str(value)) > 1:
				additional_fields_dict[key] = value

		return additional_fields_dict

	def prepare_link_to_alert(self):
		url = self.define_harp_event_url()

		return url

	def prepare_alert_subject(self, action):
		if action == 'create' or action == 'update':
			msg = f"Alert has been triggered - {self.define_subject_name()}"
		elif action == 'still_exist':
			msg = f"Alert is still exist - {self.define_subject_name()}"
		else:
			msg = f"Alert has been closed - {self.define_subject_name()}"

		return msg

	def render_image(self):
		if self.rendered_graph:
			time_now = datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f')
			file_img = settings.TELEGRAM_TEMP_FILES + "/{0}.png".format(time_now)
			decoded_image = base64.b64decode(self.rendered_graph['res_img'].split(",")[1])
			with open(file_img, 'wb') as fp:
				fp.write(decoded_image)
				fp.close()

			file_to_read = open(file_img, 'rb')

			return file_to_read
		else:
			return None

	def telegram_processor(self, action):
		for telegram_chat in self.telegram_id:
			event_body = {
				'telegram_chat_id': telegram_chat,
				'title': self.prepare_alert_subject(action),
				'text': None,
				'button_url': self.prepare_link_to_alert(),
				'facts': self.prepare_additional_fields(),
				'image_body': self.render_image(),
				'image_url': None
			}

			try:
				req = requests.post(
					url=settings.TELEGRAM_SERVICE,
					data=json.dumps(event_body),
					headers={"Content-Type": "application/json"},
					timeout=30
				)

				if req.status_code != 200:
					log.error(
						msg=f"Error: Can`t push notification to Telegram. Teams return status code {req.status_code}\nResult: {req.json()}\ndata: {json.dumps(event_body)}",
						extra={"tags": {}}
					)
				else:
					pass
					log.info(
						msg=f"Successfully pushed event to Telegram - {req.json()}",
						extra={"tags": {}}
					)

				return req
			except Exception as err:
				log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}")

	def create_chat(self):
		if settings.TELEGRAM_ACTIVE == "false":
			return 'fake_recipient_id'

		log.debug(
			msg=f"Create Telegram Chat",
			extra={"tags": {}}
		)

		self.telegram_processor(action='create')

	def update_chat(self):
		if settings.TELEGRAM_ACTIVE == "false":
			return 'fake_recipient_id'

		log.debug(
			msg=f"Update Telegram Chat",
			extra={"tags": {}}
		)

		self.telegram_processor(action='update')

	def still_exist_chat(self):
		if settings.TELEGRAM_ACTIVE == "false":
			return 'fake_recipient_id'

		log.debug(
			msg=f"Still Exist Telegram Chat",
			extra={"tags": {}}
		)

		self.telegram_processor(action='still_exist')

	def close_chat_comment(self):
		if settings.TELEGRAM_ACTIVE == "false":
			return 'fake_recipient_id'

		log.debug(
			msg=f"Close Telegram Chat",
			extra={"tags": {}}
		)

		self.telegram_processor(action='close')


class VerifyTelegram(object):
	def __init__(self, telegram_id, action_type, alert_id):
		self.telegram_id = telegram_id
		self.bot = None
		self.action_type = action_type
		self.alert_id = alert_id

	def define_harp_event_url(self):
		if settings.DOCKER_SERVER_IP:
			notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
		else:
			notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

		return notification_url

	@staticmethod
	def notify_message():
		msg = f"This is the test message from Harp Event console."

		return msg

	def verify_telegram(self):
		if self.action_type == 'assign':
			try:
				for telegram_chat in self.telegram_id:
					event_body = {
						'telegram_chat_id': telegram_chat,
						'title': f'Alert has been assigned to Telegram chat - {telegram_chat}',
						'text': self.notify_message(),
						'button_url': self.define_harp_event_url(),
						'facts': {},
						'image_body': None,
						'image_url': None
					}

					req = requests.post(
						url=settings.TELEGRAM_SERVICE,
						data=json.dumps(event_body),
						headers={"Content-Type": "application/json"},
						timeout=30
					)

					log.info(
						msg=f"Telegram chat has been verified: {telegram_chat}\nResult: {req.json()}"
					)

				return True
			except Exception as err:
				log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}")

				return False
		else:
			return True
