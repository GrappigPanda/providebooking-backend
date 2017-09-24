from sqlalchemy import and_
from sqlalchemy import func
from datetime import datetime
from dateutil import relativedelta

import math

from almanac.models import ScheduleTable as Schedule, db
from almanac.exc.exceptions import DAOException


class BaseDAO(object):
    def _assert_valid_duration(self, start_time, end_time):
        """
        Makes sure all durations are valid.

        :param datetime.datetime start_time: The date at which the schedule
        opens.
        :param datetime.datetime end_time: The date at which the schedule
        closes.
        :raises: DAOException
        :rtype: NoneType
        :returns: None
        """
        if start_time >= end_time:
            raise DAOException(
                'Invalid start time. Start must be before the end.'
            )

        if end_time.day != start_time.day:
            raise DAOException(
                'A schedule must start and end in the same day.'
            )

        min_diff = math.ceil((end_time - start_time).total_seconds()/60)
        if min_diff not in [5, 15, 30, 60]:
            if min_diff > 60 and min_diff % 60 == 0:
                return

            raise DAOException(
                'Invalid duration. Attempted duration is not of valid length.'
            )

    def _assert_schedule_exists(self, start_time, end_time, scheduled_user_id):
        """
        Asserts that the scheduled user has a schedule open for the event.

        :param datetime.datetime start_time: The date at which the schedule
        opens.
        :param datetime.datetime end_time: The date at which the schedule
        closes.
        :param str scheduled_user_id: The user ID to retrieve schedules for.
        :raises: DAOException
        :rtype: NoneType
        :returns: None
        """
        if end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)
        if start_time.tzinfo is not None:
            start_time = start_time.replace(tzinfo=None)

        schedule = db.session.query(
            Schedule
        ).filter(
            Schedule.user_id == scheduled_user_id,
            func.lower(Schedule.utc_duration) <= start_time,
            func.upper(Schedule.utc_duration) >= end_time,
        )

        schedule = schedule.first()

        if schedule is None:
            raise DAOException(
                'Invalid event. User does not have an open schedule time slot '
                'for the requested booking.'
            )

    def _assert_not_in_past(self, start_time, end_time):
        """
        Asserts the new schedule is not in the past.

        :param datetime.datetime start_time: The date at which the schedule
        opens.
        :param datetime.datetime end_time: The date at which the schedule
        closes.
        :raises: DAOException
        :rtype: NoneType
        :returns: Nothing
        """
        current_time = datetime.now(start_time.tzinfo)

        if start_time < current_time:
            raise DAOException(
                'Cannot create schedules in the past.'
            )

    def _add_time_period(self, time_period_offset):
        """
        Adds a time period offset to get the current period.

        :param int time_period_offset: The offset for teh current time period.
        :rtype: datetime
        :return: The current date + time period offset.
        """
        time_now = datetime.today()

        time_now = time_now + relativedelta.relativedelta(
            months=time_period_offset
        )

        return time_now

