from logger.logging import service_logger
from harp_daemon.models.active_alerts import ActiveAlerts
from harp_daemon.models.notifications import Notifications
import ujson as json
import traceback
import harp_daemon.settings as settings
from harp_daemon.plugins.kafka_consumer import KafkaConsumeMessages
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class ReassignNotification(object):
	def __init__(self, kafka_topic):
		self.kafka_topic = kafka_topic
		self.old_environment_id = None
		self.unassigned_env_id = 1

	def start_consumer(self):
		consumer = KafkaConsumeMessages(kafka_topic=self.kafka_topic).start_consumer()

		while True:
			msg = consumer.poll(5.0)

			if msg is None:
				continue
			if msg.error():
				log.error(msg=f"Consumer error: {msg.error()}")
				continue
				
			parsed_json = None
			try:
				parsed_json = json.loads(msg.value().decode('utf-8'))

				if parsed_json['type'] == 'delete':
					self.old_environment_id = parsed_json['body']['environment_id']
					self.update_env_to_default()
			except ConnectionResetError as err:
				log.warning(msg=f"Can`t connect to Kafka: {err}\nStack: {traceback.format_exc()}\n{parsed_json}")
				continue
			except Exception as err:
				log.error(msg=f"Exception in Thread: {err}\nStack: {traceback.format_exc()}\n{parsed_json}")
				exit()

	@tracer.start_as_current_span("get_active_notifications")
	def get_active_notifications(self):
		get_active_events = ActiveAlerts.get_active_event_by_environment(environment_id=self.old_environment_id)
		all_active_events = [single_event.json()['alert_id'] for single_event in get_active_events]

		return all_active_events

	@tracer.start_as_current_span("get_all_notifications")
	def get_all_notifications(self):
		get_active_events = Notifications.get_active_event_by_environment(environment_id=self.old_environment_id)
		all_active_events = [single_event.json()['id'] for single_event in get_active_events]

		return all_active_events

	@tracer.start_as_current_span("update_env_to_default")
	def update_env_to_default(self):
		try:
			all_notifications = self.get_active_notifications() + self.get_all_notifications()

			for notification_id in all_notifications:
				ActiveAlerts.update_exist_event(
					event_id=notification_id,
					data={'studio': self.unassigned_env_id}
				)

				Notifications.update_exist_event(
					event_id=notification_id,
					data={'studio': self.unassigned_env_id}
				)
		except Exception as err:
			log.error(msg=f"Can`t update Env from {self.old_environment_id} to {self.unassigned_env_id}\nERROR: {err}")
			return f'Can`t update Env from {self.old_environment_id} to {self.unassigned_env_id}'

	def main(self):
		try:
			self.start_consumer()
		except Exception as err:
			log.error(msg=f"Exception during processing message from Kafka: {err}")
