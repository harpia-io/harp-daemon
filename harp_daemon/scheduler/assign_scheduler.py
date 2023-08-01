from logger.logging import service_logger
from harp_daemon.models.assigne import Assign
from harp_daemon.models.notifications import Notifications
from harp_daemon.models.active_alerts import ActiveAlerts
from harp_daemon.handlers.resubmit_processor import Resubmit
from datetime import datetime
from harp_daemon.tools.prometheus_metrics import Prom
from jira import JIRA
import uuid
import ujson as json
import harp_daemon.settings as settings
import traceback
from harp_daemon.handlers.get_bot_config import bot_config
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class AssignProcessor(object):
	def __init__(self):
		self.event_id = str(uuid.uuid4())
		self.alert_id = None
		self.jira = None
		self.single_assign = None
		self.exist_notification = None
		self.bot_config = bot_config(bot_name='jira')

	@tracer.start_as_current_span("init_jira_connection")
	def init_jira_connection(self):
		self.jira = JIRA(
			options={'server': self.bot_config['JIRA_SERVER'], 'verify': False},
			basic_auth=(self.bot_config['JIRA_USER'], self.bot_config['JIRA_PASSWORD']),
			timeout=settings.JIRA_TIMEOUT
		)

	@tracer.start_as_current_span("resubmit_event")
	def resubmit_event(self):
		event = Resubmit(alert_id=self.alert_id, event_id=self.event_id)
		event.process_resubmit()

	@tracer.start_as_current_span("cancel_assign")
	def cancel_assign(self):
		Notifications.update_exist_event(event_id=self.alert_id, data={"assign_status": 0})
		# log.debug(
		# 	msg=f"Assign status was reset to default in Notifications",
		# 	extra={"event_id": self.event_id}
		# )

		Assign.delete_assign(alert_id=self.alert_id)
		# log.debug(
		# 	msg=f"Assign was removed from Assign table",
		# 	extra={"event_id": self.event_id}
		# )

		ActiveAlerts.update_exist_event(event_id=self.alert_id, data={"assign_status": 0})
		# log.debug(
		# 	msg=f"Assign status was reset to default in Active Alerts",
		# 	extra={"event_id": self.event_id}
		# )

	@tracer.start_as_current_span("check_assign_duration")
	def check_assign_duration(self, assign_time):
		now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
		fmt = '%Y-%m-%d %H:%M:%S'
		time1 = datetime.strptime(str(assign_time), fmt)
		time2 = datetime.strptime(str(now), fmt)
		# log.debug(msg=f"Check assign duration: time1 {time1}, time2: {time2}")
		difference = time1 - time2
		# log.debug(msg=f"Check assign duration: difference {difference}, difference.seconds: {difference.seconds}")
		if time2 > time1:
			# log.debug(
			# 	msg=f"Assign was expired. Assign to {assign_time}, current time - {now}",
			# 	extra={"event_id": self.event_id}
			# )
			return True
		else:
			return False

	@tracer.start_as_current_span("get_exist_notification")
	def get_exist_notification(self):
		get_notification = Notifications.get_notification_by_id(event_id=self.alert_id)
		exist_notification = [single_notification.json() for single_notification in get_notification][0]

		return exist_notification

	@tracer.start_as_current_span("check_if_event_active")
	def check_if_event_active(self):
		# log.debug(msg=f"Check if event active - {self.exist_notification}", extra={"event_id": self.event_id})

		if self.exist_notification['notification_status'] != 0:
			return True
		else:
			return False

	@tracer.start_as_current_span("check_assign_resubmit")
	def check_assign_resubmit(self):
		# log.debug(msg=f"Start checking Assign resubmit - {self.single_assign}", extra={"event_id": self.event_id})
		if self.check_if_event_active():
			if self.single_assign['resubmit'] > 0:
				now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
				then = self.exist_notification['last_update_ts']
				fmt = '%Y-%m-%d %H:%M:%S'
				time1 = datetime.strptime(str(then), fmt)
				time2 = datetime.strptime(str(now), fmt)
				difference = (time2 - time1).total_seconds()
				resubmit_seconds = self.single_assign['resubmit'] * 60 * 60
				if difference > resubmit_seconds:
					# log.debug(
					# 	msg=f"Assign event will be resubmitted. Last update ts: {time1}. Current: {time2}. Resubmit: {self.single_assign['resubmit']}, Diff: {difference}",
					# 	extra={"event_id": self.event_id}
					# )
					return True

	@tracer.start_as_current_span("check_jira_status")
	def check_jira_status(self):
		if json.loads(self.single_assign['notification_fields'])['jira_closed'] == 1:
			self.init_jira_connection()

			jira_issue = json.loads(self.single_assign['notification_fields'])['project'].split("/")
			issue = self.jira.issue(jira_issue[-1])

			# log.debug(msg=f"Check JIRA {jira_issue[-1]} Status: {issue.fields.status}")
			if issue.fields.status == "Closed":
				self.cancel_assign()

				return "cancel_assign"

	@tracer.start_as_current_span("get_assigns")
	def get_assigns(self):
		assign = Assign.get_all_assign()
		all_assigns = [single_event.json() for single_event in assign]

		return all_assigns

	@tracer.start_as_current_span("check_assign")
	def check_assign(self):
		if self.check_assign_duration(assign_time=self.single_assign['time_to']):
			self.cancel_assign()
		elif self.check_assign_resubmit():
			self.resubmit_event()

	@tracer.start_as_current_span("check_email")
	def check_email(self):

		self.check_assign()

	@tracer.start_as_current_span("check_jira")
	def check_jira(self):
		if self.check_jira_status() is None:
			self.check_assign()

	@tracer.start_as_current_span("check_skype")
	def check_skype(self):
		self.check_assign()

	@tracer.start_as_current_span("check_teams")
	def check_teams(self):
		self.check_assign()

	@tracer.start_as_current_span("check_telegram")
	def check_telegram(self):
		self.check_assign()

	@tracer.start_as_current_span("check_pagerduty")
	def check_pagerduty(self):
		self.check_assign()

	@tracer.start_as_current_span("check_sms")
	def check_sms(self):
		self.check_assign()

	@tracer.start_as_current_span("check_voice")
	def check_voice(self):
		self.check_assign()

	@tracer.start_as_current_span("check_whatsapp")
	def check_whatsapp(self):
		self.check_assign()

	@tracer.start_as_current_span("check_signl4")
	def check_signl4(self):
		self.check_assign()

	@tracer.start_as_current_span("check_slack")
	def check_slack(self):
		self.check_assign()

	@tracer.start_as_current_span("check_webhook")
	def check_webhook(self):
		self.check_assign()

	@tracer.start_as_current_span("process_assign")
	def process_assign(self):
		# log.debug(msg=f"Start processing Assigns", extra={"event_id": self.event_id})
		all_assigns = self.get_assigns()

		for single_assign in all_assigns:
			try:
				# log.debug(msg=f"Process - {single_assign}", extra={"event_id": self.event_id})
				self.single_assign = single_assign
				self.alert_id = single_assign['alert_id']
				self.exist_notification = self.get_exist_notification()

				if single_assign['notification_type'] == 2:
					self.check_email()
				elif single_assign['notification_type'] == 3:
					self.check_jira()
				elif single_assign['notification_type'] == 4:
					self.check_skype()
				elif single_assign['notification_type'] == 5:
					self.check_teams()
				elif single_assign['notification_type'] == 6:
					self.check_telegram()
				elif single_assign['notification_type'] == 7:
					self.check_pagerduty()
				elif single_assign['notification_type'] == 8:
					self.check_sms()
				elif single_assign['notification_type'] == 9:
					self.check_voice()
				elif single_assign['notification_type'] == 10:
					self.check_whatsapp()
				elif single_assign['notification_type'] == 11:
					self.check_signl4()
				elif single_assign['notification_type'] == 12:
					self.check_slack()
				elif single_assign['notification_type'] == 13:
					self.check_webhook()
				else:
					log.error(
						msg=f"Unknown notification type in Assign - {single_assign}",
						extra={"event_id": self.event_id}
					)
			except Exception as err:
				log.error(
					msg=f"Can`t process assign - {single_assign}. Error: {err}. Stack: {traceback.format_exc()}",
					extra={"event_id": self.event_id}
				)


@Prom.ALERT_ASSIGN_PROCESSOR.time()
@tracer.start_as_current_span("assign_processor")
def assign_processor():
	event = AssignProcessor()
	event.process_assign()
