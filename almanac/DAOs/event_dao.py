import dateutil
import logging
import pytz

from sqlalchemy import or_, extract
from sqlalchemy.orm import aliased

from almanac.DAOs.base_dao import BaseDAO
from almanac.exc.exceptions import DAOException
from almanac.models import UserTable as User
from almanac.models import db
from almanac.models import EventTable as Event
from almanac.utils.database_utils import exec_and_commit


class EventDAO(BaseDAO):
    """
    Handles event management.
    """

    def get_for_scheduling_user(self, user_id, time_offset=0):
        """
        Returns all booked events for a scheduling user.

        :param str user_id: The user to retrieve scheduled events for.
        :rtype: list[EventTable]
        :return: All booked events for a user.
        """
        current_timeperiod = self._add_time_period(
            time_offset
        )

        return db.session.query(Event).filter(
            Event.scheduling_user_id == user_id,
            Event.month_number == current_timeperiod.month,
        ).all()

    def get_for_scheduled_user(self, user_id, time_offset=0):
        """
        Returns all booked events for a scheduled user.

        :param str user_id: The user to retrieve scheduled events for.
        :rtype: list[EventTable]
        :return: All booked events for a user.
        """
        current_timeperiod = self._add_time_period(
            time_offset
        )

        return Event.query.filter(
            Event.scheduled_user_id == user_id,
            Event.month_number == current_timeperiod.month,
        ).all()

    def get_by_event_id(self, user_id, event_id):
        """
        Returns the information for an event.

        :param str user_id: Either the scheduled or scheduling user.
        :param str event_id: The event to retrieve
        :rtype: EventTable
        :return: The requested event.
        """
        scheduled = aliased(User)
        scheduling = aliased(User)

        event = db.session.query(
            Event,
            scheduled,
            scheduling,
        ).filter(
            or_(
                Event.scheduled_user_id == user_id,
                Event.scheduling_user_id == user_id,
            ),
            Event.public_id == event_id,
        ).join(
            scheduled, Event.scheduled_user_id == scheduled.public_id,
        ).join(
            scheduling, Event.scheduling_user_id == scheduling.public_id,
        ).first()

        if event is None:
            logging.error(
                'Failed to retrieve event ({0}) for user {1}.'.format(
                    event_id,
                    user_id,
                )
            )
            raise DAOException(
                'Requested event not found. Please refresh and try again.'
            )

        return event

    def create_new_event(
            self,
            scheduling_user_id,
            scheduled_user_id,
            localized_start_time,
            localized_end_time,
            local_tz,
            notes=None,
            *,
            skip_commit=False
    ):
        """
        Creates a new event for the scheduled user.

        :param str scheduling_user_id: The user creating the event.
        :param str scheduled_user_id: The user who's time is being purchased
        :param datetime.datetime localized_start_time: The localized start.
          Converted to UTC for insert.
        :param datetime.datetime localized_end_time: The localized end
        :param str local_tz: The timezone in which the event was created.
        :param str notes: Any notes written by the scheduling user.
        :param bool skip_commit: An optional flag used to indicate if we want
        to create the object and add to DB delta, but not commit it just yet.
        Used mostly for facade methods which roll back if the event doesn't
        fully complete (transaction doesn't finalize, &c.).
        :rtype: EventTable
        :return: The newly created event.
        """
        start_time = pytz.timezone(local_tz).localize(
            dateutil.parser.parse(localized_start_time)
        )
        end_time = pytz.timezone(local_tz).localize(
            dateutil.parser.parse(localized_end_time)
        )

        start_time = start_time.astimezone(pytz.timezone('UTC'))
        end_time = end_time.astimezone(pytz.timezone('UTC'))

        self._assert_not_in_past(start_time, end_time)

        self._assert_schedule_exists(
            start_time,
            end_time,
            scheduled_user_id
        )

        self._assert_valid_duration(start_time, end_time)

        new_event = Event(
            start_time,
            end_time,
            scheduling_user_id,
            scheduled_user_id,
            notes
        )

        exec_and_commit(db.session.add, new_event, skip_commit=skip_commit)

        return new_event

    def eradicate_event(self, event_public_id):
        """
        Handles event rollbacks in case the payment fails.

        :param str event_public_id: The event we're wanting to delete
        :rtype: EventTable
        :return: The event which was eradicated.
        """
        found_event = db.session.query(
            Event
        ).filter_by(
            public_id=event_public_id
        ).first()

        if found_event is None:
            raise DAOException(
                'Failed to delete event. Event does not exist.'
            )

        exec_and_commit(db.session.delete, found_event)

        return found_event
