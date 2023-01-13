from logger.logging import service_logger
import harp_daemon.settings as settings
import requests
import ujson as json
import traceback

log = service_logger()


class GenerateAutoVoice(object):
	def __init__(self, phone_numbers: list, event_id, notification_output, object_name, service, alert_name, alert_id, description, studio):
		self.phone_numbers = phone_numbers
		self.event_id = event_id
		self.notification_output = notification_output
		self.alert_id = alert_id
		self.object_name = object_name
		self.service = service
		self.alert_name = alert_name
		self.description = description
		self.studio = studio

	def define_subject_name(self):
		subject_name = f"{self.alert_name}"

		return subject_name

	def define_harp_event_url(self):
		if settings.DOCKER_SERVER_IP:
			notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
		else:
			notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

		return notification_url

	def _prepare_additional_fields(self):
		additional_fields_lst = []

		if self.description:
			additional_fields_lst.append(f"Description: {self.description}")

		if self.studio and self.studio != "Other":
			additional_fields_lst.append(f"Studio: {self.studio}")

		if self.service and self.service != "Other":
			additional_fields_lst.append(f"Service: {self.service}")

		if self.object_name:
			additional_fields_lst.append(f"Host: {self.object_name}")

		if 'current' in self.notification_output:
			additional_fields_lst.append(f"Current Alert Output: {self.notification_output['current']}")

		return '.'.join(additional_fields_lst)

	def prepare_create_message(self, action):
		if action == 'create' or action == 'update':
			msg = f"New alert created. Name - {self.define_subject_name()}."
		elif action == 'still_exist':
			msg = f"Alert still exist. Name - {self.define_subject_name()}"
		else:
			msg = f"Alert closed. Name - {self.define_subject_name()}"

		return msg

	def voice_processor(self, action):
		for single_phone in self.phone_numbers:
			event_body = {
				'to_number': single_phone,
				'body': self.prepare_create_message(action),
				'event_id': self.event_id
			}

			try:
				req = requests.post(
					url=settings.VOICE_SERVICE,
					data=json.dumps(event_body),
					headers={"Content-Type": "application/json"},
					timeout=30
				)

				if req.status_code != 200:
					log.error(
						msg=f"Error: Can`t push notification to Voice Service. Return status code {req.status_code}\nURL: {single_phone}\ndata: {json.dumps(event_body)}",
						extra={"tags": {"event_id": self.event_id}}
					)
				else:
					pass
					log.info(
						msg=f"Successfully pushed event to Voice - {req} - {single_phone}",
						extra={"tags": {"event_id": self.event_id}}
					)

				return req
			except Exception as err:
				log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}")

	def create_chat(self):
		if settings.VOICE_ACTIVE == "false":
			return 'fake_recipient_id'

		self.voice_processor(action='create')

	def update_chat(self):
		if settings.VOICE_ACTIVE == "false":
			return 'fake_recipient_id'

		self.voice_processor(action='update')

	def still_exist_chat(self):
		if settings.VOICE_ACTIVE == "false":
			return 'fake_recipient_id'

		self.voice_processor(action='still_exist')

	def close_chat_comment(self):
		if settings.VOICE_ACTIVE == "false":
			return 'fake_recipient_id'

		self.voice_processor(action='close')
