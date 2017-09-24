from almanac.models import BaseTable
from almanac.models import db


class ContactTable(BaseTable):
    """
    Houses the schedules of contact form submissions.
    """
    __tablename__ = 'contact_submissions'

    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    message = db.Column(db.TEXT, nullable=False)

    def __init__(self, name, email, message):
        super().__init__()

        self.name = name
        self.email = email
        self.message = message

    def __repr__(self):
        return 'Name: {0} - Email: {1} - id: {2}'.format(
            self.name,
            self.email,
            self.id
        )
