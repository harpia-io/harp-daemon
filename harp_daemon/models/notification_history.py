from logger.logging import service_logger
import datetime
from harp_daemon.plugins.db import Session, Base
import sqlalchemy
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
session = Session()
tracer = get_tracer().get_tracer(__name__)


class NotificationHistory(Base):
    __tablename__ = 'notification_history'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    alert_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    notification_output = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    notification_action = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    comments = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    time_stamp = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)

    def json(self):
        return {
            'alert_id': self.alert_id,
            'notification_output': self.notification_output,
            'notification_action': self.notification_action,
            'comments': self.comments,
            'time_stamp': self.time_stamp,
        }

    @classmethod
    @tracer.start_as_current_span("get_reopen_history")
    def get_reopen_history(cls, alert_id):
        time_shift = datetime.datetime.utcnow() - datetime.timedelta(minutes=60)

        queries = session.query(cls.alert_id).filter(
            cls.alert_id == alert_id,
            cls.notification_action == "Reopen event",
            cls.time_stamp > time_shift
        ).all()

        reopen_count = [single_event.alert_id for single_event in queries]

        return len(reopen_count)

    @classmethod
    @tracer.start_as_current_span("update_alert_history")
    def update_alert_history(cls, alert_id, notification_output, notification_action):
        data = {
            "alert_id": alert_id,
            "notification_output": notification_output,
            "notification_action": notification_action
        }
        cls.add_new_event(data=data)

    @classmethod
    @tracer.start_as_current_span("add_new_event")
    def add_new_event(cls, data: dict):
        try:
            notification = NotificationHistory(**data)
            session.add(notification)
            session.commit()
            # cls.add_new_event_aerospike(data)
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot add new event to Notification History - {err}\nData: {data}")

    @classmethod
    @tracer.start_as_current_span("update_exist_event")
    def update_exist_event(cls, event_id: int, data: dict):
        try:
            session.query(cls).filter(
                cls.id == event_id
            ).update(data)

            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot update exist event in Notification History - {err}\nData: {data}")

    @classmethod
    @tracer.start_as_current_span("delete_exist_event")
    def delete_exist_event(cls, event_id: int):
        try:
            session.query(cls).filter(
                cls.id == event_id
            ).delete(synchronize_session='fetch')

            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot delete exist event from Notification History - {err}\nEvent ID: {event_id}")

    @classmethod
    @tracer.start_as_current_span("get_history_by_id")
    def get_history_by_id(cls, event_id):
        queries = session.query(cls).filter(
            cls.alert_id == event_id
        ).all()

        return queries
