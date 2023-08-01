from harp_daemon.db import db
from logger.logging import service_logger
from harp_daemon.plugins.tracer import get_tracer

log = service_logger()
tracer = get_tracer().get_tracer(__name__)


class Configuration(db.Model):
    __tablename__ = 'configuration'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    severity_mapping = db.Column(db.Text(4294000000))
    notification_type_mapping = db.Column(db.Text(4294000000))

    def json(self):
        return {
            'severity_id_mapping': self.severity_mapping,
            'notification_type_id_mapping': self.notification_type_mapping,
        }

    @classmethod
    @tracer.start_as_current_span("get_configuration")
    def get_configuration(cls):
        db.session.commit()
        queries = cls.query.all()

        return queries
