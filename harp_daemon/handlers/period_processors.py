from logger.logging import service_logger
from datetime import datetime

log = service_logger()


def in_time_period(start_time, end_time, now_time):
	if start_time < end_time:
		return start_time <= now_time <= end_time
	else:
		return now_time >= start_time or now_time <= end_time


def check_notification_period(notification):
	fmt = '%H:%M'
	period = notification['procedure']['notification_period']

	if period:
		time_from = datetime.strptime(str(period['from']), fmt).strftime(fmt)
		time_to = datetime.strptime(str(period['to']), fmt).strftime(fmt)
		now = datetime.utcnow().strftime('%H:%M')
		return in_time_period(start_time=time_from, end_time=time_to, now_time=now)
	else:
		return True
