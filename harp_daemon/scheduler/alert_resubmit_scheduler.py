from logger.logging import service_logger
from harp_daemon.models.notifications import Notifications
from harp_daemon.models.active_alerts import ActiveAlerts
from harp_daemon.handlers.resubmit_processor import Resubmit
from harp_daemon.models.procedures import Procedures
from harp_daemon.models.notification_history import NotificationHistory
from harp_daemon.tools.prometheus_metrics import Prom
from datetime import datetime
import uuid
import traceback
import ujson as json
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class AlertResubmit(object):
	def __init__(self):
		self.event_id = None
		self.alert_id = None
		self.jira = None
		self.single_event = None
		self.exist_notification = None

	@tracer.start_as_current_span("resubmit_event")
	def resubmit_event(self):
		event = Resubmit(alert_id=self.alert_id, event_id=self.event_id)
		event.process_resubmit()

	@tracer.start_as_current_span("get_exist_notification")
	def get_exist_notification(self):
		get_notification = Notifications.get_notification_by_id(event_id=self.alert_id)
		exist_notification = [single_notification.json() for single_notification in get_notification][0]

		return exist_notification

	@tracer.start_as_current_span("get_procedure")
	def get_procedure(self, procedure_id):
		# log.debug(msg=f"Get exist procedure: {procedure_id}", extra={"event_id": self.event_id})
		get_procedure = Procedures.get_procedure_by_id(procedure_id=procedure_id)
		try:
			exist_procedure = [single_notification.json() for single_notification in get_procedure][0]
		except IndexError:
			log.error(msg=f"Can`t find procedure id - {procedure_id} in Harp. Please check it")
			raise

		# log.debug(msg=f"Procedure: {exist_procedure}", extra={"event_id": self.event_id})

		return exist_procedure

	@tracer.start_as_current_span("get_history")
	def get_history(self):
		get_history = NotificationHistory.get_history_by_id(event_id=self.alert_id)
		last_event_history = [single_history.json() for single_history in get_history][-1]

		# log.debug(msg=f'Get history for event: {self.alert_id}, {last_event_history}', extra={"event_id": self.event_id})

		return last_event_history['time_stamp']

	@tracer.start_as_current_span("check_resubmit")
	def check_resubmit(self, resubmit_hours):
		# log.debug(msg=f"Start checking event resubmit - {self.single_event}", extra={"event_id": self.event_id})
		if resubmit_hours > 0:
			now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
			then = self.get_history()
			fmt = '%Y-%m-%d %H:%M:%S'
			time1 = datetime.strptime(str(then), fmt)
			time2 = datetime.strptime(str(now), fmt)
			difference = (time2 - time1).total_seconds()
			resubmit_seconds = resubmit_hours * 60 * 60
			if difference > resubmit_seconds:
				# log.debug(
				# 	msg=f"Event event will be resubmitted. Last update ts: {time1}. Current: {time2}. Resubmit: {resubmit_hours}, Diff: {difference}",
				# 	extra={"event_id": self.event_id}
				# )
				return True

	@tracer.start_as_current_span("get_resubmit_hours")
	def get_resubmit_hours(self):
		# procedure = get_scenario_by_id(scenario_id=self.exist_notification['procedure_id'])
		procedure = self.get_procedure(procedure_id=self.exist_notification['procedure_id'])

		if self.single_event['notification_type'] == 2:
			resubmit_hours = json.loads(procedure['email_fields'])
		elif self.single_event['notification_type'] == 3:
			resubmit_hours = json.loads(procedure['jira_fields'])
		elif self.single_event['notification_type'] == 4:
			resubmit_hours = json.loads(procedure['skype_fields'])
		elif self.single_event['notification_type'] == 5:
			resubmit_hours = json.loads(procedure['teams_fields'])
		elif self.single_event['notification_type'] == 6:
			resubmit_hours = json.loads(procedure['telegram_fields'])
		elif self.single_event['notification_type'] == 7:
			resubmit_hours = json.loads(procedure['pagerduty_fields'])
		elif self.single_event['notification_type'] == 8:
			resubmit_hours = json.loads(procedure['sms_fields'])
		elif self.single_event['notification_type'] == 9:
			resubmit_hours = json.loads(procedure['voice_fields'])
		elif self.single_event['notification_type'] == 10:
			resubmit_hours = json.loads(procedure['whatsapp_fields'])
		elif self.single_event['notification_type'] == 11:
			resubmit_hours = json.loads(procedure['signl4_fields'])
		elif self.single_event['notification_type'] == 12:
			resubmit_hours = json.loads(procedure['slack_fields'])
		elif self.single_event['notification_type'] == 13:
			resubmit_hours = json.loads(procedure['webhook_fields'])
		else:
			resubmit_hours = None
			log.error(msg=f"Unknown notification type in Resubmit - {self.single_event}", extra={"event_id": self.event_id})

		if 'resubmit' in resubmit_hours:
			# log.debug(msg=f"Return resubmit hours - {resubmit_hours}", extra={"event_id": self.event_id})
			return resubmit_hours['resubmit']

	@tracer.start_as_current_span("prepare_resubmit_event")
	def prepare_resubmit_event(self):
		resubmit_hours = self.get_resubmit_hours()

		if resubmit_hours:
			if self.check_resubmit(resubmit_hours):
				self.resubmit_event()

	@tracer.start_as_current_span("process_resubmit")
	def process_resubmit(self):
		# log.debug(msg=f"Start processing Resubmit")
		get_active_events = ActiveAlerts.get_all_active_events()
		all_active_events = [single_event.json() for single_event in get_active_events]

		# log.debug(msg=f"Active events for resubmit: {all_active_events}")

		for single_event in all_active_events:
			self.event_id = str(uuid.uuid4())
			try:
				# log.debug(msg=f"Process Resubmit - {single_event}", extra={"event_id": self.event_id})
				self.single_event = single_event
				self.alert_id = single_event['alert_id']
				self.exist_notification = self.get_exist_notification()

				self.prepare_resubmit_event()

			except Exception as err:
				log.warning(
					msg=f"Can`t process resubmit - {single_event}. Error: {err}. Stack: {traceback.format_exc()}",
					extra={"event_id": self.event_id}
				)


@Prom.ALERT_RESUBMIT_PROCESSOR.time()
@tracer.start_as_current_span("alert_resubmit_processor")
def alert_resubmit_processor():
	event = AlertResubmit()
	event.process_resubmit()
