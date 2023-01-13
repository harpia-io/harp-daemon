from logger.logging import service_logger
import datetime
import ujson as json
from harp_daemon.plugins.db import Session, Base
import sqlalchemy
from retry_decorator import *

log = service_logger()
session = Session()


class Notifications(Base):
    __tablename__ = 'notifications'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True, unique=True)
    name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False, unique=True)
    studio = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, unique=True)
    ms = sqlalchemy.Column(sqlalchemy.String(40), nullable=False, unique=True)
    source = sqlalchemy.Column(sqlalchemy.String(100), nullable=False, unique=True)
    object_name = sqlalchemy.Column(sqlalchemy.String(100), nullable=False, unique=True)
    service = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)
    severity = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    department = sqlalchemy.Column(sqlalchemy.String(100), default=json.dumps([]))
    output = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    additional_fields = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    additional_urls = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    actions = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    description = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    ms_alert_id = sqlalchemy.Column(sqlalchemy.String(100), unique=True)
    recipient_id = sqlalchemy.Column(sqlalchemy.String(255))
    assigned_to = sqlalchemy.Column(sqlalchemy.String(255), default=json.dumps({}))
    action_by = sqlalchemy.Column(sqlalchemy.String(255), default=json.dumps({}))
    image = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    total_duration = sqlalchemy.Column(sqlalchemy.BigInteger, default=0, nullable=False)
    notification_status = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)
    assign_status = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)
    snooze_expire_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default='1970-01-01 00:00:01', nullable=False)
    sticky = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)
    procedure_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    last_update_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), onupdate=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
    last_create_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), nullable=False)

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'studio': self.studio,
            'ms': self.ms,
            'source': self.source,
            'object_name': self.object_name,
            'service': self.service,
            'severity': self.severity,
            'department': self.department,
            'output': self.output,
            'additional_fields': self.additional_fields,
            'additional_urls': self.additional_urls,
            'actions': self.actions,
            'description': self.description,
            'ms_alert_id': self.ms_alert_id,
            'recipient_id': self.recipient_id,
            'image': self.image,
            'total_duration': self.total_duration,
            'notification_status': self.notification_status,
            'assign_status': self.assign_status,
            'snooze_expire_ts': self.snooze_expire_ts,
            'sticky': self.sticky,
            'procedure_id': self.procedure_id,
            'last_update_ts': self.last_update_ts,
            'last_create_ts': self.last_create_ts,
            'assigned_to': self.assigned_to,
            'action_by': self.action_by
        }

    @classmethod
    def get_notification(cls, ms_alert_id, alert_name, source, studio, ms, object_name):
        session.commit()
        queries = session.query(cls).filter(
            cls.ms_alert_id == ms_alert_id,
            cls.name == alert_name,
            cls.source == source,
            cls.studio == studio,
            cls.ms == ms,
            cls.object_name == object_name
        ).all()

        return queries

    @classmethod
    def get_notification_by_id(cls, event_id):
        session.commit()
        queries = session.query(cls).filter(
            cls.id == event_id
        ).all()

        return queries

    @classmethod
    def get_active_event_by_environment(cls, environment_id):
        session.commit()
        queries = session.query(cls).filter(
            cls.studio == environment_id
        ).all()

        return queries

    @classmethod
    @retry(Exception, tries=3, timeout_secs=0.1)
    def update_exist_event(cls, event_id: int, data: dict):
        try:
            session.query(cls).filter(
                cls.id == event_id
            ).update(data)

            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot update exist event in Notifications - {err}\nalert_id: {event_id}\nData: {data}")

    @classmethod
    def add_new_event(cls, data: dict):
        notification = Notifications(**data)
        try:
            session.add(notification)
            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot add new event to Notifications - {err}\nData: {data}")

        return notification.json()

    @classmethod
    def delete_notification(cls, notification_id: int):
        try:
            session.query(cls).filter(
                cls.id == notification_id
            ).delete(synchronize_session='fetch')
            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot delete exist event to Notifications - {err}\nNotification ID: {notification_id}")
