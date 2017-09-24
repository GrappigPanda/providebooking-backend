from almanac.models import BaseTable
from almanac.models import db


class EmailQueueTable(BaseTable):
    """
    Works as a poor-man's queue for emailing.
    """
    __tablename__ = 'email_queue'

    email_to = db.Column(db.String(128), nullable=False)
    email_from = db.Column(db.String(128), nullable=False)
    subject = db.Column(db.TEXT, nullable=False)
    body = db.Column(db.String(256), nullable=False)

    def __init__(self, email_to, email_from, subject, body):
        super().__init__()

        self.email_to = email_to
        self.email_from = email_from
        self.subject = subject
        self.body = body

    def __repr__(self):
        return 'To {0} from {1} w/ subject {2}'.format(
            self.email_to,
            self.email_from,
            self.subject,
        )


