from logger.logging import service_logger
import requests
import ujson as json
import harp_daemon.settings as settings
import traceback
import os

log = service_logger()


class GenerateAutoTeams(object):
	def __init__(self, event_id, rendered_graph, notification_output, object_name, service, alert_name, alert_id, teams_id, description, studio, graph_url=None, additional_fields=None, additional_urls=None):
		self.teams_id = teams_id
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
		self.additional_urls = additional_urls
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

	def prepare_alert_subject(self, action):
		if action == 'create' or action == 'update':
			msg = f"Alert has been triggered - {self.define_subject_name()}"
		elif action == 'still_exist':
			msg = f"Alert is still exist - {self.define_subject_name()}"
		else:
			msg = f"Alert has been closed - {self.define_subject_name()}"

		return msg

	def teams_processor(self, action):
		for teams_chat in self.teams_id:
			event_body = {
				'teams_webhook': teams_chat,
				'title': self.prepare_alert_subject(action=action),
				'text': None,
				'button_url': {"Open Alert": self.define_harp_event_url()},
				'facts': self.prepare_additional_fields()
			}

			try:
				req = requests.post(
					url=settings.TEAMS_SERVICE,
					data=json.dumps(event_body),
					headers={"Content-Type": "application/json"},
					timeout=30
				)

				if req.status_code != 200:
					log.error(
						msg=f"Error: Can`t push notification to Slack. Slack return status code {req.status_code}\nResult: {req.json()}\ndata: {json.dumps(event_body)}",
						extra={"tags": {}}
					)
				else:
					pass
					log.info(
						msg=f"Successfully pushed event to Slack - {req.json()}",
						extra={"tags": {}}
					)

				return req
			except Exception as err:
				log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}")

	def create_chat(self):
		if settings.TEAMS_ACTIVE == "false":
			return 'fake_recipient_id'

		self.teams_processor(action='create')

	def update_chat(self):
		if settings.TEAMS_ACTIVE == "false":
			return 'fake_recipient_id'

		self.teams_processor(action='update')

	def still_exist_chat(self):
		if settings.TEAMS_ACTIVE == "false":
			return 'fake_recipient_id'

		self.teams_processor(action='still_exist')

	def close_chat_comment(self):
		if settings.TEAMS_ACTIVE == "false":
			return 'fake_recipient_id'

		self.teams_processor(action='close')


class VerifyTeams(object):
	def __init__(self, teams_id, action_type, alert_id):
		self.teams_id = teams_id
		self.bot = None
		self.action_type = action_type
		self.alert_id = alert_id

	@staticmethod
	def notify_message():
		msg = f"This is the test message from Harp Event console"

		return msg

	def verify_teams(self):
		if self.action_type == 'assign':
			for teams_chat in self.teams_id:
				event_body = {
					'teams_webhook': teams_chat,
					'title': "Assign alert to Teams Channel",
					'text': self.notify_message(),
					'button_url': {},
					'facts': {}
				}

				try:
					req = requests.post(
						url=settings.TEAMS_SERVICE,
						data=json.dumps(event_body),
						headers={"Content-Type": "application/json"},
						timeout=30
					)

					if req.status_code != 200:
						log.error(
							msg=f"Error: Can`t push notification to Slack. Slack return status code {req.status_code}\nResult: {req.json()}\ndata: {json.dumps(event_body)}",
							extra={"tags": {}}
						)
					else:
						pass
						log.info(
							msg=f"Successfully pushed event to Slack - {req.json()}",
							extra={"tags": {}}
						)

					return req
				except Exception as err:
					log.error(msg=f"Error: {err}, Stack: {traceback.format_exc()}")
		else:
			return True
