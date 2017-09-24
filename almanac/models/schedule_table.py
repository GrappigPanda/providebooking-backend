from psycopg2._range import DateTimeRange
from sqlalchemy.dialects.postgresql.ranges import TSTZRANGE, TSRANGE
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from psycopg2.extras import DateTimeTZRange

from almanac.models import BaseTable
from almanac.models import db


class ScheduleTable(BaseTable):
    """
    Houses the schedules of users.
    """
    __tablename__ = 'schedules'

    # Foreign keys.
    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.public_id'),
        nullable=False
    )

    # Actual schedule stuff.
    utc_duration = db.Column(TSRANGE, nullable=False)
    local_duration = db.Column(TSTZRANGE, nullable=False)

    day_number = db.Column(db.SmallInteger, nullable=False)
    month_number = db.Column(db.SmallInteger, nullable=False)

    # tz stuff
    local_tz = db.Column(db.String, nullable=False)

    ExcludeConstraint(('utc_duration', '&&'))
    ExcludeConstraint(('local_duration', '&&'))

    @property
    def local_tz_open(self): return self.local_duration.lower

    @property
    def local_tz_end(self): return self.local_duration.upper

    @property
    def utc_open(self): return self.utc_duration.lower

    @property
    def utc_end(self): return self.utc_duration.upper

    def __init__(self, open_date, end_date, user_id, local_tz):
        super().__init__()
        self.utc_duration = DateTimeRange(open_date, end_date)
        self.local_duration = DateTimeTZRange(
            self._localize(self.utc_duration.lower, local_tz),
            self._localize(self.utc_duration.upper, local_tz),
        )

        self.day_number = open_date.day
        self.month_number = open_date.month
        self.local_tz = local_tz

        self.user_id = str(user_id)

    def __repr__(self):
        return 'Open: {0} -> End: {1} -- For User: {2}'.format(
            self.utc_open,
            self.utc_end,
            self.user_id
        )
