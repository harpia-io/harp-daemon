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


class GenerateAutoWebhook(object):
	def __init__(self, event_id, rendered_graph, notification_output, object_name, service, alert_name, alert_id, webhooks, description, studio, graph_url=None, additional_fields=None):
		self.webhooks = webhooks
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

	@staticmethod
	def webhook_get_request(webhook_url):
		try:
			req = requests.get(
				url=webhook_url,
				timeout=30
			).json()

			log.info(msg=f"Webhook was triggered. Status:\n{req}")

			return req

		except Exception as err:
			log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}")

	@staticmethod
	def format_post_headers(post_headers):
		headers = {"Content-Type": "application/json"}

		if post_headers:
			try:
				header_json = json.loads(post_headers)
			except Exception as err:
				header_json = {}
				log.error(msg=f"Header is not a JSON\nInput: {post_headers}\nERROR: {err}")

			headers.update(header_json)

		return headers

	@staticmethod
	def format_post_body(post_body):
		body = {}

		if post_body:
			try:
				body_json = json.loads(post_body)
			except Exception as err:
				body_json = {}
				log.error(msg=f"POST Body is not a JSON\nInput: {post_body}\nERROR: {err}")

			body.update(body_json)

		return body

	@staticmethod
	def webhook_post_request(webhook_url, body, headers, auth):
		try:
			if auth:
				req = requests.post(
					url=webhook_url,
					data=json.dumps(body),
					headers=headers,
					auth=(auth['login'], auth['password']),
					timeout=30,
					verify=False
				).json()
			else:
				req = requests.post(
					url=webhook_url,
					data=json.dumps(body),
					headers=headers,
					timeout=30,
					verify=False
				).json()

			log.info(msg=f"Webhook was triggered. Status:\n{req.json()}")

			return req

		except Exception as err:
			log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}\nInput: webhook_url: {webhook_url}, body: {body}, headers: {headers}, auth: {auth}")

	def webhook_processor(self, action):
		webhook_responses = []
		for single_webhook in self.webhooks:
			if single_webhook['http_method'] == "GET":
				webhook_status = self.webhook_get_request(
					webhook_url=single_webhook['url']
				)
				webhook_responses.append(webhook_status)
			else:
				webhook_status = self.webhook_post_request(
					webhook_url=single_webhook['url'],
					body=self.format_post_body(single_webhook['json']),
					auth=single_webhook['basicAuth'],
					headers=self.format_post_headers(single_webhook['headers'])
				)
				webhook_responses.append(webhook_status)

		return webhook_responses

	def create_chat(self):
		log.debug(
			msg=f"Create Webhook Chat",
			extra={"tags": {}}
		)

		result = self.webhook_processor(action='create')

		return result

	@staticmethod
	def update_chat():
		return 'fake_recipient_id'

	@staticmethod
	def still_exist_chat():
		return 'fake_recipient_id'

	@staticmethod
	def close_chat_comment():
		return 'fake_recipient_id'
