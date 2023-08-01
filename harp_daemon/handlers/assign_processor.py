from logger.logging import service_logger
from harp_daemon.models.assigne import Assign
import harp_daemon.notification_plugins as handlers
import ujson as json
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer_get = get_tracer()
tracer = tracer_get.get_tracer(__name__)


class AssignProcessor(object):
	def __init__(self, notification):
		self.notification = notification
		self.recipient_id = None

	@tracer.start_as_current_span("email_recipients")
	def email_recipients(self):
		recipients = json.loads(self.notification['exist_assign']['notification_fields'])['recipients']

		return {'recipients': recipients}

	@tracer.start_as_current_span("define_recipient_id")
	def define_recipient_id(self):
		recipient_id = self.notification['exist_assign']['recipient_id']

		return recipient_id

	@tracer.start_as_current_span("define_jira_recipient_id")
	def define_jira_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['project']

		return recipient_id

	@tracer.start_as_current_span("define_skype_recipient_id")
	def define_skype_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['ids']

		return recipient_id

	@tracer.start_as_current_span("define_teams_recipient_id")
	def define_teams_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['ids']

		return recipient_id

	@tracer.start_as_current_span("define_telegram_recipient_id")
	def define_telegram_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['ids']

		return recipient_id

	@tracer.start_as_current_span("define_slack_recipient_id")
	def define_slack_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['ids']

		return recipient_id

	@tracer.start_as_current_span("define_webhook_recipient_id")
	def define_webhook_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['webhooks']

		return recipient_id

	@tracer.start_as_current_span("define_pagerduty_recipient_id")
	def define_pagerduty_recipient_id(self):
		api_key = json.loads(self.notification['exist_assign']['notification_fields'])['ids']
		recipient_id = self.notification['exist_assign']['recipient_id']

		return recipient_id, api_key

	@tracer.start_as_current_span("define_sms_recipient_id")
	def define_sms_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['ids']

		return recipient_id

	@tracer.start_as_current_span("define_voice_recipient_id")
	def define_voice_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['ids']

		return recipient_id

	@tracer.start_as_current_span("define_signl4_recipient_id")
	def define_signl4_recipient_id(self):
		recipient_id = json.loads(self.notification['exist_assign']['notification_fields'])['ids']

		return recipient_id

	@tracer.start_as_current_span("process_assign")
	def process_assign(self, notification_action):
		"""
		"email": 2,
		"jira": 3,
		"skype": 4,
		"teams": 5,
		"telegram": 6
		"pagerduty": 7
		"sms": 8
		"voice": 9
		"whatsapp": 10
		"signl4": 11
		"slack": 12
		"webhook": 13
		"""
		assign = self.notification['exist_assign']

		if assign['notification_type'] == 2:
			log.debug(
				msg=f"Notification type for assign is Email",
				extra={"tags": {"event_id": self.notification["event_id"]}}
			)

			event = handlers.EmailHandler(notification=self.notification, action=notification_action)
			self.recipient_id = event.process_email(
				action=notification_action,
				recipients=self.email_recipients()['recipients'],
				recipient_id=self.define_recipient_id()
			)

			if self.recipient_id:
				log.debug(
					msg=f"Update recipient_id in Assign",
					extra={"tags": {"event_id": self.notification["event_id"]}}
				)
				Assign.update_exist_event(
					event_id=self.notification['exist_alert_body']['id'],
					data={'recipient_id': self.recipient_id}
				)

		elif assign['notification_type'] == 3:
			log.debug(
				msg=f"Notification type for assign is JIRA",
				extra={"tags": {"event_id": self.notification["event_id"]}}
			)
			event = handlers.JiraHandler(notification=self.notification, action=notification_action)
			event.process_jira(
				action=notification_action,
				recipient_id=self.define_jira_recipient_id()
			)

		elif assign['notification_type'] == 4:
			log.debug(
				msg=f"Notification type for assign is Skype",
				extra={"tags": {"event_id": self.notification["event_id"]}}
			)
			event = handlers.SkypeHandler(notification=self.notification, action=notification_action)
			event.process_skype(
				action=notification_action,
				skype_id=self.define_skype_recipient_id()
			)

		elif assign['notification_type'] == 5:
			log.debug(
				msg=f"Notification type for assign is Teams",
				extra={"tags": {"event_id": self.notification["event_id"]}}
			)
			event = handlers.TeamsHandler(notification=self.notification, action=notification_action)
			event.process_teams(
				action=notification_action,
				teams_id=self.define_teams_recipient_id()
			)

		elif assign['notification_type'] == 6:
			log.debug(
				msg=f"Notification type for assign is Telegram",
				extra={"tags": {"event_id": self.notification["event_id"]}}
			)
			event = handlers.TelegramHandler(notification=self.notification, action=notification_action)
			event.process_telegram(
				action=notification_action,
				telegram_id=self.define_telegram_recipient_id()
			)

		elif assign['notification_type'] == 7:
			event = handlers.PagerdutyHandler(notification=self.notification, action=notification_action)
			recipient_id, api_key = self.define_pagerduty_recipient_id()
			self.recipient_id = event.process_pagerduty(
				action=notification_action,
				api_key=api_key,
				recipient_id=recipient_id
			)

			if self.recipient_id:
				Assign.update_exist_event(
					event_id=self.notification['exist_alert_body']['id'],
					data={'recipient_id': self.recipient_id}
				)

		elif assign['notification_type'] == 8:
			event = handlers.SMSHandler(notification=self.notification, action=notification_action)
			self.recipient_id = event.process_sms(
				action=notification_action
			)
			if self.recipient_id:
				Assign.update_exist_event(
					event_id=self.notification['exist_alert_body']['id'],
					data={'recipient_id': self.recipient_id}
				)

		elif assign['notification_type'] == 9:
			log.debug(
				msg=f"Notification type for assign is Voice",
				extra={"tags": {"event_id": self.notification["event_id"]}}
			)
			event = handlers.VoiceHandler(notification=self.notification, action=notification_action)
			self.recipient_id = event.process_voice(
				action=notification_action
			)
			if self.recipient_id:
				log.debug(
					msg=f"Update recipient_id in Assign",
					extra={"tags": {"event_id": self.notification["event_id"]}}
				)
				Assign.update_exist_event(
					event_id=self.notification['exist_alert_body']['id'],
					data={'recipient_id': self.recipient_id}
				)

		elif assign['notification_type'] == 11:
			event = handlers.Signl4Handler(notification=self.notification, action=notification_action)
			self.recipient_id = event.process_signl4(
				action=notification_action
			)
			if self.recipient_id:
				Assign.update_exist_event(
					event_id=self.notification['exist_alert_body']['id'],
					data={'recipient_id': self.recipient_id}
				)

		elif assign['notification_type'] == 12:
			event = handlers.SlackHandler(notification=self.notification, action=notification_action)
			self.recipient_id = event.process_slack(
				action=notification_action
			)
			if self.recipient_id:
				Assign.update_exist_event(
					event_id=self.notification['exist_alert_body']['id'],
					data={'recipient_id': self.recipient_id}
				)

		elif assign['notification_type'] == 13:
			event = handlers.WebhookHandler(notification=self.notification, action=notification_action)
			self.recipient_id = event.process_webhook(
				action=notification_action
			)
			if self.recipient_id:
				Assign.update_exist_event(
					event_id=self.notification['exist_alert_body']['id'],
					data={'recipient_id': self.recipient_id}
				)

		else:
			log.error(
				msg=f"Incorrect notification_type in assign - {assign}",
				extra={"tags": {"event_id": self.notification["event_id"]}}
			)
