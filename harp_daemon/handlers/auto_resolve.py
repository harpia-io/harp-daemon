from logger.logging import service_logger
from harp_daemon.models.active_alerts import ActiveAlerts
from harp_daemon.models.notifications import Notifications
from harp_daemon.models.notification_history import NotificationHistory
import traceback
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer_get = get_tracer()
tracer = tracer_get.get_tracer(__name__)


class AutoResolve(object):
	def __init__(self, alert_ids, event_id):
		self.alert_ids = alert_ids
		self.event_id = event_id

	@staticmethod
	@tracer.start_as_current_span("remove_from_active_alerts")
	def remove_from_active_alerts(single_alert):
		ActiveAlerts.delete_exist_event(event_id=single_alert)

	@staticmethod
	@tracer.start_as_current_span("update_notifications")
	def update_notifications(single_alert):
		data = {
			'severity': 0,
			'notification_status': 0
		}
		Notifications.update_exist_event(
			event_id=single_alert,
			data=data
		)

	@staticmethod
	@tracer.start_as_current_span("update_notification_history")
	def update_notification_history(single_alert):
		data = {
			"alert_id": single_alert,
			"notification_output": "Resolved by recovery mechanism",
			"notification_action": "Close event"
		}
		NotificationHistory.add_new_event(data=data)

	@tracer.start_as_current_span("process_resolve")
	def process_resolve(self):
		try:
			for single_alert in self.alert_ids:
				self.remove_from_active_alerts(single_alert)
				self.update_notifications(single_alert)
				self.update_notification_history(single_alert)
		except Exception as err:
			log.error(
				msg=f"Can`t process event - {err}. Trace: {traceback.format_exc()}",
				extra={"tags": {"event_id": self.event_id}}
			)
