from psycopg2._range import DateTimeRange
from sqlalchemy import func

import pytz
import enum

from almanac.exc.exceptions import DAOException
from almanac.DAOs.base_dao import BaseDAO
from almanac.models import db
from almanac.models import ScheduleTable as Schedule
from almanac.models import UserTable as User
from almanac.utils.database_utils import exec_and_commit


class TimePeriodEnum(enum.Enum):
    MONTH = 0

    __value_lookup = {
        "month": MONTH
    }

    @staticmethod
    def lookup_enum_type(enum_type):
        """
        Returns a time period value based

        :param str enum_type: A time period type like "month", "week".
        :rtype: TimePeriodEnum
        :return: The enum value corresponding to the input.
        """
        try:
            return TimePeriodEnum.__value_lookup[enum_type.lower()]
        except KeyError:
            raise DAOException("Invalid time period type.")


class ScheduleDAO(BaseDAO):
    """
    Handles a user's schedule.
    """

    def get(self, user_id, time_period=TimePeriodEnum.MONTH,
            time_period_offset=0, detected_timezone='UTC'):
        """
        Retrieves a user's schedule for the specified time period.

        :param str user_id: The user id to retrieve the schedule for.
        :param TimePeriodEnum time_period: The time period to retrieve.
        Typically month.
        :param int time_period_offset: The offset for teh current time period.
        :rtype: ScheduleTable
        :return: A schedule row (or None) corresponding to the request.
        """
        current_timeperiod = self._add_time_period(
            time_period_offset
        )

        return db.session.query(Schedule).filter(
            Schedule.user_id == user_id,
            Schedule.month_number == current_timeperiod.month,
        ).all()

    def get_by_schedule_id(self, schedule_id):
        """
        Retrives a schedule by its ID.

        :param int schedule_id: The schedule to retrieve.
        :rtype: ScheduleTable
        :return: The queried Schedule Table.
        """
        return db.session.query(Schedule).filter(
            Schedule.public_id == schedule_id
        ).first()

    def post(self, start_time, end_time, user_id):
        """
        Handles the creation of a new schedule.

        :param datetime.datetime start_time: The date at which the schedule
        opens.
        :param datetime.datetime end_time: The date at which the schedule
        closes.
        :param str user_id: The user to create the schedule for.
        :rtype: ScheduleTable
        :return: The newly scheduled table.
        """
        self._assert_valid_duration(start_time, end_time)
        self._assert_no_duration_overlap(start_time, end_time, user_id)
        self._assert_not_in_past(start_time, end_time)

        user_info = db.session.query(User).filter(
            User.public_id == user_id
        ).first()

        if user_info is None:
            raise DAOException('Invalid user requested. Try again.')

        new_schedule = Schedule(
            start_time,
            end_time,
            user_id,
            user_info.local_tz
        )

        exec_and_commit(db.session.add, new_schedule)

        return new_schedule

    def put(self, schedule_id, start_time, end_time, user_id):
        """
        Updates a schedule to new duration.

        :param int schedule_id: The schedule to update.
        :param datetime.datetime start_time: The date at which the schedule
        opens.
        :param datetime.datetime end_time: The date at which the schedule
        closes.
        :param str user_id: The user to create the schedule for.
        :rtype: ScheduleTable
        :return: The newly scheduled table.
        """
        self._assert_valid_duration(start_time, end_time)

        schedule = self.get_by_schedule_id(schedule_id)

        if schedule is None:
            raise DAOException('Requested schedule is invalid. Try again.')

        if start_time < schedule.utc_open.replace(tzinfo=None) or end_time > schedule.utc_end.replace(tzinfo=None):
            self._assert_no_duration_overlap(start_time, end_time, user_id)

        rows_affected = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.public_id == schedule_id
        ).update({
            'utc_duration': DateTimeRange(start_time, end_time),
        })

        db.session.commit()

        if rows_affected == 0:
            raise DAOException(
                'Failed to update schedule. Schedule not found.'
            )

        return self.get_by_schedule_id(schedule_id)

    def delete(self, user_id, schedule_id):
        """
        Deletes a schedule by its id.

        :param str user_id: The user to delete the schedule for.
        :param int schedule_id: The schedule to delete.
        """
        rows_affected = Schedule.query.filter(
            Schedule.user_id == user_id,
            Schedule.public_id == schedule_id,
        ).delete()

        db.session.commit()

        if rows_affected == 0:
            raise DAOException(
                'Failed to delete schedule. Schedule not found.'
            )

    def _assert_no_duration_overlap(self, start_time, end_time, user_id):
        """
        Retrieves all of a users schedules and asserts that there is no
        schedule overlap.

        :param datetime.datetime start_time: The date at which the schedule
        opens.
        :param datetime.datetime end_time: The date at which the schedule
        closes.
        :param str user_id: The user ID to filter by.
        :raises: DAOException
        :rtype: NoneType
        :returns: Nothing
        """
        schedules = db.session.query(Schedule).filter(
            func.lower(Schedule.utc_duration) <= start_time,
            func.upper(Schedule.utc_duration) >= end_time,
            Schedule.user_id == user_id,
            Schedule.day_number == end_time.day,
        ).all()

        if not schedules:
            return

        raise DAOException(
            "Invalid schedule. This overlaps with a previous schedule."
        )

    def _assert_valid_duration(self, start_time, end_time):
        """
        Makes sure all durations are valid.

        :param datetime.datetime start_time: The date at which the schedule
        opens.
        :param datetime.datetime end_time: The date at which the schedule
        closes.
        :raises: DAOException
        :rtype: NoneType
        :returns: Nothing
        """
        if start_time >= end_time:
            raise DAOException(
                "Invalid start time. Start must be before the end."
            )


