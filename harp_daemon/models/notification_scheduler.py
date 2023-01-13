from logger.logging import service_logger
from datetime import datetime
from harp_daemon.plugins.db import Session, Base
import sqlalchemy

log = service_logger()
session = Session()


class NotificationScheduler(Base):
    __tablename__ = 'notification_scheduler'

    alert_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, primary_key=True)
    channel = sqlalchemy.Column(sqlalchemy.String(255), nullable=False, primary_key=True)
    scenario_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    action = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    execute = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False)

    def json(self):
        return {
            'alert_id': self.alert_id,
            'channel': self.channel,
            'scenario_id': self.scenario_id,
            'action': self.action,
            'execute': self.execute
        }

    @classmethod
    def get_events_to_process(cls):
        queries = session.query(cls).filter(
            cls.execute < datetime.utcnow()
        ).all()

        events_to_process = [single_event.json() for single_event in queries]

        return events_to_process

    @classmethod
    def add_new_event(cls, data: dict):
        notification = NotificationScheduler(**data)
        try:
            session.add(notification)
            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot add new event to NotificationScheduler - {err}\nData: {data}")

    @classmethod
    def update_exist_event(cls, alert_id: int, data: dict):
        try:
            session.query(cls).filter(
                cls.alert_id == alert_id
            ).update(data)

            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot update exist event in NotificationScheduler - {err}\nData: {data}")

    @classmethod
    def delete_exist_event(cls, alert_id: int):
        try:
            session.query(cls).filter(
                cls.alert_id == alert_id
            ).delete(synchronize_session='fetch')

            session.commit()
        except Exception as err:
            session.rollback()
            log.error(msg=f"Cannot delete exist event from NotificationScheduler - {err}\nAlert ID: {alert_id}")
