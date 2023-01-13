import requests
from logger.logging import service_logger
import harp_daemon.settings as settings
import traceback
import requests_cache

requests_cache.install_cache(cache_name='cache', backend='memory', expire_after=settings.REQUESTS_CACHE_EXPIRE_SECONDS,
                             allowable_methods='GET')
log = service_logger()


def get_from_environments(env_id):
    endpoint = f'{settings.ENVIRONMENTS_HOST}/{env_id}'
    try:
        req = requests.get(url=endpoint, headers={"Accept": "application/json", "Content-Type": "application/json"},
                           timeout=10)
        return req.json()
    except Exception as err:
        log.error(msg=f"Error: {err}, stack: {traceback.format_exc()}")
        return {'msg': {}}


def env_id_to_name(env_id):
    get_environments = get_from_environments(env_id=env_id)
    if get_environments['msg']:
        environments_list = get_environments['msg']['env_name']

        return environments_list
    else:
        return 'Other'


