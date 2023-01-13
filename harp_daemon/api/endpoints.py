from logger.logging import service_logger
import traceback
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
import harp_daemon.settings as settings
from typing import Optional, List, Dict, Union
from harp_daemon.models.configuration import Configuration
from harp_daemon.notification_processors.skype_processor import VerifySkype
from harp_daemon.notification_processors.email_processor import VerifyEmail
from harp_daemon.notification_processors.teams_processor import VerifyTeams
from harp_daemon.notification_processors.telegram_processor import VerifyTelegram
from harp_daemon.notification_processors.jira_processor import VerifyJIRA
from harp_daemon.handlers.resubmit_processor import Resubmit
from harp_daemon.handlers.auto_resolve import AutoResolve
import ujson as json
import uuid
from harp_daemon.settings import NOTIFICATION_TYPE_MAPPING


log = service_logger()
router = APIRouter(prefix=settings.URL_PREFIX)


class RecipientsVerify(BaseModel):
    recipients: list
    action_type: str
    alert_id: int


class EventResolver(BaseModel):
    ids: list[int]


class ResubmitEvent(BaseModel):
    alert_id: int
    event_id: str


@router.get('/configuration')
async def get_harp_configuration():
    """
    Get list of Org services
    """

    log.info(
        msg=f"Request to get harp configuration",
        extra={"tags": {}}
    )

    try:
        final_config = {}
        """
        Get Harp configuration
        """
        prepare_config = Configuration.get_configuration()
        configuration = [conf.json() for conf in prepare_config][0]
        for conf_name, conf_body in configuration.items():
            final_config[conf_name] = json.loads(conf_body)

        return final_config
    except Exception as err:
        log.error(
            msg=f"Failed to get org services to edit\nERROR: {err}\nStack: {traceback.format_exc()}",
            extra={"tags": {}}
        )

        raise HTTPException(status_code=500, detail=f"Backend error: {err}")


@router.post('/recipient_verify')
async def recipients_verify(row_data: RecipientsVerify):
    """
    Get list of Org services
    """

    log.info(
        msg=f"Request to get harp configuration",
        extra={"tags": {}}
    )

    try:
        data = row_data.dict()
        log.debug(msg=f"Receive event from recipient_verify endpoint\n{data}")
        recipient_list = data['recipients']
        if data['action_type'] == 'assign':
            for recipient in recipient_list:
                recipient_type = recipient['recipient_type']
                recipient_id = recipient['recipient_id']
                action_type = data['action_type']
                alert_id = data['alert_id']

                if recipient_type == 4:
                    notification_type = VerifySkype(skype_id=recipient_id, action_type=action_type, alert_id=alert_id)
                    if notification_type.verify_skype():
                        return {"status": f"Successfully added new recipient {recipient_id} to notification"}, 200
                    else:
                        return {"status": f"Recipient {recipient_id} not found"}, 404
                elif recipient_type == 5:
                    notification_type = VerifyTeams(teams_id=recipient_id, action_type=action_type, alert_id=alert_id)
                    if notification_type.verify_teams():
                        return {"status": f"Successfully added new recipient {recipient_id} to notification"}, 200
                    else:
                        return {"status": f"Recipient {recipient_id} not found"}, 404
                elif recipient_type == 3:
                    notification_type = VerifyJIRA(recipients=recipient_id, action_type=action_type, alert_id=alert_id)
                    if notification_type.verify_jira():
                        return {"status": f"Successfully added new recipient {recipient_id} to notification"}, 200
                    else:
                        return {"status": f"Recipient {recipient_id} not found"}, 404
                elif recipient_type == 6:
                    notification_type = VerifyTelegram(telegram_id=recipient_id, action_type=action_type, alert_id=alert_id)
                    if notification_type.verify_telegram():
                        return {"status": f"Successfully added new recipient {recipient_id} to notification"}, 200
                    else:
                        return {"status": f"Recipient {recipient_id} not found"}, 404
                elif recipient_type == 2:
                    notification_type = VerifyEmail(recipients=recipient_id, action_type=action_type, alert_id=alert_id)
                    if notification_type.verify_email():
                        return {"status": f"Successfully added new recipient {recipient_id} to notification"}, 200
                    else:
                        return {"status": f"Recipient {recipient_id} not found"}, 404
                else:
                    return {"status": f"Unknown notification type - {recipient_type}"}, 400
        else:
            return {"status": f"Successfully added new recipient to notification"}, 200

    except Exception as err:
        log.error(
            msg=f"Failed to get org services to edit\nERROR: {err}\nStack: {traceback.format_exc()}",
            extra={"tags": {}}
        )

        raise HTTPException(status_code=500, detail=f"Backend error: {err}")


@router.post('/auto_resolve')
async def auto_resolve(row_data: EventResolver):
    """
    Get list of Org services
    """

    log.info(
        msg=f"Request to get harp configuration",
        extra={"tags": {}}
    )

    try:
        data = row_data.dict()
        event_id = str(uuid.uuid4())

        log.debug(
            msg=f"Receive event from auto_resolve endpoint\n{data}",
            extra={"tags": {"event_id": event_id}}
        )

        processor = AutoResolve(alert_ids=data['ids'], event_id=event_id)
        processor.process_resolve()

        log.debug(
            msg=f"Result of auto resolve",
            extra={"tags": {"event_id": event_id}}
        )

        return {"status": f"Resolved alerts"}

    except Exception as err:
        log.error(
            msg=f"Failed to get org services to edit\nERROR: {err}\nStack: {traceback.format_exc()}",
            extra={"tags": {}}
        )

        raise HTTPException(status_code=500, detail=f"Backend error: {err}")


@router.post('/resubmit_event')
async def resubmit_event(row_data: ResubmitEvent):
    """
    Get list of Org services
    """

    log.info(
        msg=f"Request to get harp configuration",
        extra={"tags": {}}
    )

    try:
        data = row_data.dict()
        log.debug(msg=f"Receive event from resubmit_event endpoint\n{data}")

        alert_id = data['alert_id']
        event_id = data['event_id']

        event = Resubmit(event_id=event_id, alert_id=alert_id)
        status = event.process_resubmit()

        if status:
            return {"status": f"Can`t resubmit: {status}"}, 500
        else:
            return {"status": f"Resubmit was done"}, 200

    except Exception as err:
        log.error(
            msg=f"Failed to get org services to edit\nERROR: {err}\nStack: {traceback.format_exc()}",
            extra={"tags": {}}
        )

        raise HTTPException(status_code=500, detail=f"Backend error: {err}")


@router.get('/dictionaries/notification_types')
async def resubmit_event():
    """
    Get list of Org services
    """

    log.info(
        msg=f"Request to get harp configuration",
        extra={"tags": {}}
    )

    try:
        return NOTIFICATION_TYPE_MAPPING
    except Exception as err:
        log.error(
            msg=f"Failed to get org services to edit\nERROR: {err}\nStack: {traceback.format_exc()}",
            extra={"tags": {}}
        )

        raise HTTPException(status_code=500, detail=f"Backend error: {err}")
