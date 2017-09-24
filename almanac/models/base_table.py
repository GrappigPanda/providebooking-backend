import uuid
from datetime import datetime

import pytz

from almanac.models import db


class BaseTable(db.Model):
    """Base table which all tables should inherit from."""

    __abstract__ = True

    id = db.Column(
        db.Integer,
        autoincrement=True,
        primary_key=True,
        nullable=False,
        unique=True
    )

    public_id = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        default=datetime.utcnow()
    )

    def __init__(self):
        self.public_id = str(uuid.uuid4())

    def _localize(self, time, local_tz):
        """
        Handles localization for times.

        :param datetime time: The time to localize
        :param str local_tz: The timezone to use
        :rtype: datetime
        :return: The localized datetime object.
        """
        try:
            return pytz.utc.localize(time).astimezone(pytz.timezone(local_tz))
        except ValueError:
            return time.astimezone(pytz.timezone(local_tz))
