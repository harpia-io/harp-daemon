from logger.logging import service_logger
import datetime
from harp_daemon.plugins.db import Session, Base
import sqlalchemy

log = service_logger()
session = Session()


class Statistics(Base):
    __tablename__ = 'statistics'

    alert_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, primary_key=True, unique=True)
    close = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    create = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    reopen = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    update = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    change_severity = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    snooze = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    acknowledge = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    assign = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    update_ts = sqlalchemy.Column(sqlalchemy.TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    def json(self):
        return {
            'alert_id': self.alert_id,
            'close': self.close,
            'create': self.create,
            'reopen': self.reopen,
            'update': self.update,
            'change_severity': self.change_severity,
            'snooze': self.snooze,
            'acknowledge': self.acknowledge,
            'assign': self.assign,
            'update_ts': self.update_ts
        }

    @classmethod
    def add_new_event(cls, data: dict):
        try:
            notification = Statistics(**data)
            session.add(notification)
            session.commit()
        except Exception as err:
            session.rollback()
            log.warning(msg=f"Can`t update statistics table because of the error: {err}\nBody: {data}")

    @classmethod
    def update_counter(cls, alert_id: int, data: dict):
        try:
            session.query(cls).filter(
                cls.alert_id == alert_id
            ).update(data)

            session.commit()
        except Exception as err:
            session.rollback()
            log.warn(msg=f"Cannot update exist event in Statistics - {err}\nData: {data}")

    @classmethod
    def get_counter(cls, alert_id: int):
        query = session.query(cls).filter(
            cls.alert_id == alert_id
        ).all()

        return query
