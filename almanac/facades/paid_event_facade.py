import logging

from almanac.DAOs.address_dao import AddressDAO
from almanac.DAOs.event_dao import EventDAO
from almanac.facades.payment_facade import BraintreePaymentFacade
from almanac.exc.exceptions import (
    IntegrationException,
    FacadeException,
    DAOException)
from almanac.models import db


class EventFacade(object):
    """
    Handles complete event creation from braintree payments to DB logging to
    actual event logging.
    """

    def create_new_event(
            self,
            scheduling_user_id,
            scheduled_user_id,
            localized_start_time,
            localized_end_time,
            local_tz,
            notes,
            nonce,
            address_id=None,
    ):
        """
        Handles creation of a new event and payment processing.

        :param str scheduling_user_id: The user who is booking another's time
        :param str scheduled_user_id: Their time is being booked.
        :param datetime.datetime localized_start_time: Localized start
        :param datetime.datetime localized_end_time: The localized end
        :param str local_tz: The timezone which this was booked in.
        :param str notes: Any additional notes to add onto the event.
        :param str nonce: The nonce which determines the payment method
        being used.
        :param str address_id: An address to be used whenever billing. If not
        provided, then we attempt to find a default address.
        :rtype: EventTable
        :return: The newly created event.
        """
        if address_id is None:
            address = AddressDAO().get_default_for_user(
                scheduling_user_id
            )
        else:
            address = AddressDAO().get_by_public_id(
                address_id,
                scheduling_user_id
            )

        try:
            new_event = EventDAO().create_new_event(
                scheduling_user_id,
                scheduled_user_id,
                localized_start_time,
                localized_end_time,
                local_tz,
                notes,
                skip_commit=True
            )

            BraintreePaymentFacade().issue_new_payment(
                new_event,
                nonce,
                address
            )
        except IntegrationException as e:
            db.session.rollback()
            logging.error(
                'Failed to create new transaction with exc of {0}.'
                'Rolling back event creation for event {1}'.format(
                    e,
                    new_event.public_id
                )
            )
            raise FacadeException('Failed to finish sale.')
        except DAOException as e:
            raise e

        return new_event
