from sqlalchemy.dialects.postgresql.ranges import TSTZRANGE
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from psycopg2.extras import DateTimeTZRange

import logging
import decimal

from almanac.exc.exceptions import TableException, ModelException
from almanac.models import BaseTable
from almanac.models import SubmerchantTable
from almanac.models import db
from almanac.models import UserTable as User


class EventTable(BaseTable):
    """
    Houses the schedules of users.
    """
    __tablename__ = 'events'

    # Foreign keys.
    scheduling_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.public_id'),
        nullable=False,
        index=True
    )

    scheduled_user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.public_id'),
        nullable=False,
        index=True
    )

    utc_duration = db.Column(TSTZRANGE, nullable=False)
    scheduled_tz_duration = db.Column(TSTZRANGE, nullable=False)
    scheduling_tz_duration = db.Column(TSTZRANGE, nullable=False)

    day_number = db.Column(db.SmallInteger, nullable=False)
    month_number = db.Column(db.SmallInteger, nullable=False)

    duration = db.Column(db.Integer, nullable=False)

    total_price = db.Column(db.DECIMAL, nullable=False)
    service_fee = db.Column(db.DECIMAL, nullable=False)

    # TODO(ian): Mark this with a payment transaction ID.
    transaction_id = db.Column(db.Integer, nullable=True)

    notes = db.Column(db.String(512), nullable=True)

    ExcludeConstraint(('utc_duration', '&&'))
    ExcludeConstraint(('scheduled_tz_duration', '&&'))
    ExcludeConstraint(('scheduling_tz_duration', '&&'))

    @property
    def utc_start(self): return self.utc_duration.lower

    @property
    def utc_end(self): return self.utc_duration.upper

    @property
    def scheduled_tz_start(self): return self.scheduled_tz_duration.lower

    @property
    def scheduled_tz_end(self): return self.scheduled_tz_duration.upper

    @property
    def scheduling_tz_start(self): return self.scheduling_tz_duration.lower

    @property
    def scheduling_tz_end(self): return self.scheduling_tz_duration.upper

    def __init__(self, start_time, end_time, scheduling, scheduled,
                 notes=None):
        super().__init__()

        scheduling_user_info = db.session.query(
            User
        ).filter_by(public_id=scheduling).first()

        scheduled_user_info = db.session.query(
            User
        ).filter_by(public_id=scheduled).first()

        self.utc_duration = DateTimeTZRange(start_time, end_time)
        self._set_duration_for_user(scheduling_user_info, is_scheduling=True)
        self._set_duration_for_user(scheduled_user_info, is_scheduling=False)

        if scheduling_user_info is None or scheduled_user_info is None:
            raise ModelException('Invalid requested users.')

        self.scheduling_user_id = str(scheduling)
        self.scheduled_user_id = str(scheduled)

        self.day_number = start_time.day
        self.month_number = self.utc_duration.lower.month

        self.duration = ((end_time - start_time).seconds//60)
        if self.duration != 60:
            if self.duration >= 60 and self.duration % 60 == 0:
                pass
            else:
                self.duration %= 60

        self.total_price = self.calculate_total_price(
            self.duration,
            scheduled_user_info,
        )

        submerchant_info = db.session.query(
            SubmerchantTable
        ).filter_by(
            user_id=scheduled
        ).first()

        self.service_fee = self.calculate_service_fee(submerchant_info)

        if notes is not None:
            self.notes = notes

    def __repr__(self):
        return 'Start: {0} - End: {1} - Duration (minutes): {2} - Price {3}'.\
            format(
                self.utc_start,
                self.utc_end,
                self.duration,
                self.total_price
            )

    def calculate_total_price(self, duration, scheduled_user):
        """
        Calculates the total price for the event.

        :param int duration:
        :param UserTable scheduled_user: The user which si being scheduled.
        :rtype: float
        :return: The total price for the duration.
        """
        if scheduled_user is None:
            raise TableException(
                "Invalid user to schedule."
            )

        if scheduled_user.is_premium:
            if duration not in [5, 15, 30, 45, 60]:
                if duration >= 60 and duration % 60 == 0:
                    pass
                else:
                    raise TableException(
                        "Invalid event duration. Premium users can only accept"
                        " durations of 5, 15, 30, or 60 minutes."
                    )
        else:
            if duration not in [60]:
                if duration >= 60 and duration % 60 == 0:
                    pass
                else:
                    raise TableException(
                        "Invalid event duration. Non-premium users can only "
                        "accept durations of 60 minutes."
                    )

        if scheduled_user.is_premium:
            price_lookup = {
                5: scheduled_user.five_min_price,
                15: scheduled_user.fifteen_min_price,
                30: scheduled_user.thirty_min_price,
                65: scheduled_user.sixty_min_price,
            }

            return price_lookup[duration] + decimal.Decimal(price_lookup[duration]) * decimal.Decimal(0.026) + decimal.Decimal(0.2)
        else:
            if scheduled_user.sixty_min_price is None:
                logging.error(
                    'Attempted to create event for user {0}'
                    ', but failed because no sixty_min_price'.format(
                        scheduled_user.public_id,
                    )
                )
                raise TableException(
                    'Invalid user to be scheduled. User has no price set'
                    'for 60 minutes.'
                )

            return scheduled_user.sixty_min_price + decimal.Decimal(scheduled_user.sixty_min_price) * decimal.Decimal(0.026) + decimal.Decimal(0.2)

    def calculate_service_fee(self, submerchant):
        return self.total_price * submerchant.service_fee_percent

    def _set_duration_for_user(self, user_info, is_scheduling=True):
        localized_start = self._localize(
            self.utc_duration.lower,
            user_info.local_tz
        )

        localized_end = self._localize(
            self.utc_duration.upper,
            user_info.local_tz
        )

        if is_scheduling:
            self.scheduling_tz_duration = DateTimeTZRange(
                localized_start,
                localized_end,
            )
        else:
            self.scheduled_tz_duration = DateTimeTZRange(
                localized_start,
                localized_end,
            )
