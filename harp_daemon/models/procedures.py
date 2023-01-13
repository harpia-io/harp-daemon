from harp_daemon.db import db
from logger.logging import service_logger
import datetime

log = service_logger()


class Procedures(db.Model):
    __tablename__ = 'procedures'
    __table_args__ = (
        db.UniqueConstraint(
            'name', 'studio_id',
            name='unique_component_commit'
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    studio_id = db.Column(db.Integer, nullable=False)
    requested_by = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text(4294000000))
    thresholds = db.Column(db.Text(4294000000))
    procedure_type = db.Column(db.Integer, nullable=False)
    alert_fields = db.Column(db.Text(4294000000))
    jira_fields = db.Column(db.Text(4294000000))
    email_fields = db.Column(db.Text(4294000000))
    skype_fields = db.Column(db.Text(4294000000))
    teams_fields = db.Column(db.Text(4294000000))
    telegram_fields = db.Column(db.Text(4294000000))
    pagerduty_fields = db.Column(db.Text(4294000000))
    sms_fields = db.Column(db.Text(4294000000))
    voice_fields = db.Column(db.Text(4294000000))
    whatsapp_fields = db.Column(db.Text(4294000000))
    edited_by = db.Column(db.Integer)
    last_update_ts = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

    def json(self):
        return {
            'id': self.id,
            'name': self.name,
            'studio_id': self.studio_id,
            'requested_by': self.requested_by,
            'description': self.description,
            'thresholds': self.thresholds,
            'procedure_type': self.procedure_type,
            'alert_fields': self.alert_fields,
            'jira_fields': self.jira_fields,
            'email_fields': self.email_fields,
            'skype_fields': self.skype_fields,
            'teams_fields': self.teams_fields,
            'telegram_fields': self.telegram_fields,
            'pagerduty_fields': self.pagerduty_fields,
            'sms_fields': self.sms_fields,
            'voice_fields': self.voice_fields,
            'whatsapp_fields': self.whatsapp_fields,
            'edited_by': self.edited_by,
            'last_update_ts': self.last_update_ts
        }

    @classmethod
    def get_procedure(cls, studio_id, procedure_name):
        db.session.commit()
        queries = cls.query.filter_by(studio_id=studio_id, name=procedure_name).all()

        return queries

    @classmethod
    def get_procedure_by_id(cls, procedure_id):
        db.session.commit()
        queries = cls.query.filter_by(id=procedure_id).all()

        return queries
