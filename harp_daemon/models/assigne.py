from logger.logging import service_logger
import datetime
from harp_daemon.plugins.db import Session, Base
import sqlalchemy

log = service_logger()
session = Session()


class Assign(Base):
    __tablename__ = 'assign'

    alert_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, primary_key=True, unique=True)
    notification_type = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    notification_fields = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    description = sqlalchemy.Column(sqlalchemy.Text(4294000000))
    resubmit = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    sticky = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    recipient_id = sqlalchemy.Column(sqlalchemy.String(100))
    notification_count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    time_to = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False)
    create_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=datetime.datetime.utcnow, nullable=False)
    last_update_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    def json(self):
        return {
            'alert_id': self.alert_id,
            'notification_type': self.notification_type,
            'notification_fields': self.notification_fields,
            'description': self.description,
            'resubmit': self.resubmit,
            'sticky': self.sticky,
            'recipient_id': self.recipient_id,
            'notification_count': self.notification_count,
            'time_to': self.time_to,
            'create_ts': self.create_ts,
            'last_update_ts': self.last_update_ts
        }

    @classmethod
    def get_all_assign(cls):
        query = session.query(cls).all()

        return query

    @classmethod
    def get_assign_info(cls, event_id: int):
        query = session.query(cls).filter(
            cls.alert_id == event_id
        ).all()

        return query

    @classmethod
    def update_exist_event(cls, event_id: int, data: dict):
        session.query(cls).filter(
            cls.alert_id == event_id
        ).update(data)

        session.commit()

    @classmethod
    def delete_assign(cls, alert_id: str):
        session.query(cls).filter(
            cls.alert_id == alert_id
        ).delete()

        session.commit()
