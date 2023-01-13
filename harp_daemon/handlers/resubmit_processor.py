from logger.logging import service_logger
from harp_daemon.handlers.notification_processor import NotificationDaemon
from harp_daemon.models.notifications import Notifications
from harp_daemon.models.procedures import Procedures
import traceback
import ujson as json

log = service_logger()


class Resubmit(object):
	def __init__(self, alert_id, event_id):
		self.alert_id = alert_id
		self.event_id = event_id
		self.notification = None

	def get_notification(self):
		get_notification = Notifications.get_notification_by_id(event_id=self.alert_id)
		exist_notification = [single_notification.json() for single_notification in get_notification][0]

		return exist_notification

	@staticmethod
	def get_procedure(procedure_id):
		get_procedure = Procedures.get_procedure_by_id(procedure_id=procedure_id)
		exist_procedure = [single_notification.json() for single_notification in get_procedure][0]

		return exist_procedure

	def generate_notification_body(self):
		notification = self.get_notification()
		notification['procedure'] = self.get_procedure(procedure_id=notification['procedure_id'])
		notification['event_id'] = self.event_id

		return notification

	def define_graph_url(self):
		image = self.notification['image']

		if image:
			image_load = json.loads(image)
			if image_load:
				if 'img_url' in image_load:
					return image_load['img_url']

	def define_ms_unique_data(self):
		if self.notification['ms'] == 'zabbix':
			zabbix_data = {'zabbix': {'item.id1': self.notification['ms_alert_id']}}
			return zabbix_data
		else:
			return {}

	def decorate_notification(self):
		self.notification['alert_name'] = self.notification['name']
		self.notification['notification_output'] = json.loads(self.notification['output'])['current']
		self.notification['graph_url'] = self.define_graph_url()
		self.notification['monitoring_system'] = self.notification['ms']
		self.notification['ms_unique_data'] = self.define_ms_unique_data()
		self.notification['additional_fields'] = json.loads(self.notification['additional_fields'])
		self.notification['additional_urls'] = json.loads(self.notification['additional_urls'])
		self.notification['actions'] = json.loads(self.notification['actions'])

	def process_resubmit(self):
		# log.debug(
		# 	msg=f"Start resubmit",
		# 	extra={"tags": {"event_id": self.event_id}}
		# )
		try:
			self.notification = self.generate_notification_body()
			self.decorate_notification()
			event = NotificationDaemon(
				notification=self.notification,
				notification_action='Resubmit event'
			)
			event.process_alert(check_if_alert_ok='to_process')
		except Exception as err:
			if 'has been deleted, or its row is otherwise not present' in err:
				log.error(msg=f"Can`t resubmit event - Error: {err}\nBody: {self.notification}\nStack: {traceback.format_exc()}")
			else:
				log.error(
					msg=f"Can`t resubmit event - Error: {err}\nBody: {self.notification}\nStack: {traceback.format_exc()}",
					extra={"tags": {"event_id": self.event_id}}
				)

			return err

