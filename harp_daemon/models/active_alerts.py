from logger.logging import service_logger
import datetime
import ujson as json
from harp_daemon.plugins.db import Session, Base
import sqlalchemy
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
session = Session()
tracer = get_tracer().get_tracer(__name__)


class ActiveAlerts(Base):
    __tablename__ = 'active_alerts'

    alert_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, primary_key=True, unique=True)
    alert_name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    studio = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    ms = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    source = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    service = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    object_name = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    severity = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    notification_type = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, primary_key=True, unique=True)
    notification_status = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)
    department = sqlalchemy.Column(sqlalchemy.String(255), default=json.dumps([]))
    additional_fields = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    ms_alert_id = sqlalchemy.Column(sqlalchemy.String(255))
    total_duration = sqlalchemy.Column(sqlalchemy.BigInteger, default=0, nullable=False)
    acknowledged = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)
    assign_status = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)
    assigned_to = sqlalchemy.Column(sqlalchemy.String(255), default=json.dumps({}))
    action_by = sqlalchemy.Column(sqlalchemy.String(255), default=json.dumps({}))
    consolidation_name = sqlalchemy.Column(sqlalchemy.String(40))
    consolidation_state = sqlalchemy.Column(sqlalchemy.Integer, default=0, nullable=False)
    consolidation_id = sqlalchemy.Column(sqlalchemy.BigInteger, default=0)
    consolidation_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default='1970-01-01 00:00:01', nullable=False)
    created_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False, default=datetime.datetime.utcnow)
    downtime_expire_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False, default='1970-01-01 00:00:01')
    snooze_expire_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False, default='1970-01-01 00:00:01')
    handle_expire_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False, default='1970-01-01 00:00:01')

    def json(self):
        return {
            'alert_id': self.alert_id,
            'alert_name': self.alert_name,
            'studio': self.studio,
            'ms': self.ms,
            'source': self.source,
            'service': self.service,
            'object_name': self.object_name,
            'severity': self.severity,
            'notification_type': self.notification_type,
            'notification_status': self.notification_status,
            'department': self.department,
            'additional_fields': self.additional_fields,
            'ms_alert_id': self.ms_alert_id,
            'total_duration': self.total_duration,
            'acknowledged': self.acknowledged,
            'assign_status': self.assign_status,
            'consolidation_name': self.consolidation_name,
            'consolidation_state': self.consolidation_state,
            'consolidation_id': self.consolidation_id,
            'consolidation_ts': self.consolidation_ts,
            'created_ts': self.created_ts,
            'downtime_expire_ts': self.downtime_expire_ts,
            'snooze_expire_ts': self.snooze_expire_ts,
            'handle_expire_ts': self.handle_expire_ts,
            'assigned_to': self.assigned_to,
            'action_by': self.action_by
        }

    @classmethod
    @tracer.start_as_current_span("add_new_event")
    def add_new_event(cls, data: dict):
        notification = ActiveAlerts(**data)
        try:
            session.add(notification)
            session.commit()
        except Exception as err:
            session.rollback()
            log.warning(msg=f"Cannot add new event to Active Alerts - {err}\nData: {data}")

    @classmethod
    @tracer.start_as_current_span("get_active_event_by_id")
    def get_active_event_by_id(cls, event_id):
        session.commit()
        queries = session.query(cls).filter(
            cls.alert_id == event_id
        ).all()

        return queries

    @classmethod
    @tracer.start_as_current_span("get_active_event_by_environment")
    def get_active_event_by_environment(cls, environment_id):
        session.commit()
        queries = session.query(cls).filter(
            cls.studio == environment_id
        ).all()

        return queries

    @classmethod
    @tracer.start_as_current_span("get_all_active_events")
    def get_all_active_events(cls):
        session.commit()
        queries = session.query(cls).filter(
            cls.handle_expire_ts < datetime.datetime.utcnow(),
            cls.snooze_expire_ts < datetime.datetime.utcnow(),
            cls.downtime_expire_ts < datetime.datetime.utcnow(),
            cls.notification_type != 1,
            cls.acknowledged == 0,
            cls.assign_status == 0
        ).all()

        return queries

    @classmethod
    @tracer.start_as_current_span("update_exist_event")
    def update_exist_event(cls, event_id: int, data: dict):
        try:
            session.query(cls).filter(
                cls.alert_id == event_id
            ).update(data)

            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot update exist event in Active Alerts - {err}\nData: {data}")

    @classmethod
    @tracer.start_as_current_span("delete_exist_event")
    def delete_exist_event(cls, event_id: int):
        try:
            session.commit()
            session.query(cls).filter(
                cls.alert_id == event_id
            ).delete(synchronize_session='fetch')

            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot delete exist event from Active Alerts - {err}\nEvent ID: {event_id}")

