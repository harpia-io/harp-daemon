from logger.logging import service_logger
import harp_daemon.settings as settings
from io import BytesIO
import requests
import ujson as json
import uuid
import os

log = service_logger()
bio = BytesIO()


class GenerateAutoPagerduty(object):
	def __init__(self, event_id, notification_output, object_name, service, alert_name, alert_id, pagerduty_routing_key, description, studio, graph_url=None, additional_fields=None):
		self.pagerduty_routing_key = pagerduty_routing_key
		self.event_id = event_id
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
		self.recipient_id = None

	# def define_graph_url(self):
	# 	if self.graph_url:
	# 		return self.graph_url

	def define_subject_name(self):
		subject_name = f"{self.object_name}: {self.alert_name}"

		return subject_name

	def define_harp_event_url(self):
		if settings.DOCKER_SERVER_IP:
			notification_url = f"http://{settings.DOCKER_SERVER_IP}/#/notifications-panel?notification_id={self.alert_id}"
		else:
			notification_url = f"https://{settings.SERVICE_NAMESPACE}.harpia.io/#/notifications-panel?notification_id={self.alert_id}"

		return notification_url

	def _prepare_additional_fields(self):
		additional_fields_lst = {}
		exclude_list = ["Action URL", "Note URL", "graph_url"]

		if self.description:
			additional_fields_lst['Description'] = self.description

		if self.studio and self.studio != "Other":
			additional_fields_lst['Studio'] = self.studio

		if self.service and self.service != "Other":
			additional_fields_lst['Service'] = self.service

		if self.object_name:
			additional_fields_lst['Host'] = self.object_name

		if 'current' in self.notification_output:
			additional_fields_lst['Current Alert Output'] = self.notification_output['current']

		if 'previous' in self.notification_output:
			additional_fields_lst['Previous Alert Output'] = self.notification_output['previous']

		for key, value in self.additional_fields.items():
			if key not in exclude_list and len(str(value)) > 1:
				additional_fields_lst[key] = value

		return additional_fields_lst

	def pagerduty_processor(self, action):
		try:
			for routing_key in self.pagerduty_routing_key:
				header = {"Content-Type": "application/json"}

				payload = {
					"routing_key": routing_key,
					"event_action": action,
					"dedup_key": self.recipient_id,
					"payload": {
						"summary": self.define_subject_name(),
						"severity": "critical",
						"source": self.object_name,
						"custom_details": self._prepare_additional_fields(),
						"links": [{
							"href": self.define_harp_event_url(),
							"text": "URL To Alert Destination"
						}]
					}
				}

				response = requests.post(settings.PAGERDUTY_ENDPOINT, data=json.dumps(payload), headers=header)

				if response.json()["status"] == "success":
					pass
					# log.info(msg=f'{action} pagerduty incident')
				else:
					log.error(msg=f'Can`t {action} Pagerduty incident. Details: {response.text}. Payload: {payload}')
		except Exception as err:
			log.error(msg=f"Can`t send Pagerduty message: {err}")

	def create_event(self, recipient_id):
		if settings.PAGERDUTY_ACTIVE == "false":
			return 'fake_recipient_id'

		if recipient_id:
			self.recipient_id = recipient_id
		else:
			self.recipient_id = str(uuid.uuid4())

		self.pagerduty_processor(action='trigger')

		return str(self.recipient_id)

	def update_event(self, recipient_id):
		if settings.PAGERDUTY_ACTIVE == "false":
			return 'fake_recipient_id'

		self.recipient_id = recipient_id
		self.pagerduty_processor(action='trigger')

		return str(self.recipient_id)

	def close_event(self, recipient_id):
		if settings.PAGERDUTY_ACTIVE == "false":
			return 'fake_recipient_id'

		self.recipient_id = recipient_id
		self.pagerduty_processor(action='resolve')
