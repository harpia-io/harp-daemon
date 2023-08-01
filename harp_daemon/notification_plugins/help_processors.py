import requests
from logger.logging import service_logger
import harp_daemon.settings as settings
import traceback
from harp_daemon.plugins.tracer import get_tracer
from opentelemetry.instrumentation.requests import RequestsInstrumentor

log = service_logger()
tracer = get_tracer().get_tracer(__name__)
RequestsInstrumentor().instrument()


@tracer.start_as_current_span("check_licenses")
def check_licenses(notification_type: int, event_id):
	url = f"{settings.LICENSE_SERVICE}/{notification_type}"
	headers = {
		"Accept": "application/json",
		"Content-Type": "application/json",
		"Event-Id": event_id
	}
	try:
		req = requests.get(url=url, headers=headers, timeout=10)
		if req.status_code == 200:
			return True
		elif req.status_code == 600:
			return False
		else:
			return True  # TODO Need to add logging to identify unknown errors
	except Exception as err:
		log.error(msg=f"Error: {err}, stack: {traceback.format_exc()}")
		return {'msg': None}
