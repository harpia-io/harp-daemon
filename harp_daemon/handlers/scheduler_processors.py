import traceback

from logger.logging import service_logger
from datetime import datetime, timedelta
from harp_daemon.models.notification_scheduler import NotificationScheduler

log = service_logger()


class Scheduler(object):
	def __init__(self, alert_id, scenario_type, scenario_body, scenario_id, action_trigger_delay, action):
		self.alert_id = alert_id
		self.scenario_type = scenario_type
		self.scenario_body = scenario_body
		self.scenario_id = scenario_id
		self.action_trigger_delay = action_trigger_delay
		self.action = action

	def calculate_time_shift(self):
		if 'm' in str(self.action_trigger_delay):
			time_shift = datetime.utcnow() + timedelta(minutes=int(self.action_trigger_delay.replace('m', '')))
		elif 's' in str(self.action_trigger_delay):
			time_shift = datetime.utcnow() + timedelta(seconds=int(self.action_trigger_delay.replace('s', '')))
		elif 'h' in str(self.action_trigger_delay):
			time_shift = datetime.utcnow() + timedelta(hours=int(self.action_trigger_delay.replace('h', '')))
		elif 'd' in str(self.action_trigger_delay):
			time_shift = datetime.utcnow() + timedelta(days=int(self.action_trigger_delay.replace('d', '')))
		else:
			time_shift = datetime.utcnow() + timedelta(seconds=int(self.action_trigger_delay))

		return time_shift

	def add_new_record(self):
		body = {
			'alert_id': self.alert_id,
			'channel': self.scenario_type,
			'scenario_id': self.scenario_id,
			'action': self.action,
			'execute': self.calculate_time_shift()
		}

		try:
			NotificationScheduler.add_new_event(body)
		except Exception as err:
			log.error(msg=f"Can`t process Scheduler request to add new record - {body}\nError: {err}")

	def delete_existing_record(self):
		NotificationScheduler.delete_exist_event(alert_id=self.alert_id)

	def main(self):
		if self.action_trigger_delay == "0s":
			return True
		try:
			if self.action in ['Create event', 'Reopen event']:
				self.add_new_record()
			elif self.action == 'Close event':
				self.delete_existing_record()
				return True
		except Exception as err:
			log.error(msg=f"Can`t process Scheduler request - {err}\nTrace: {traceback.format_exc()}")






