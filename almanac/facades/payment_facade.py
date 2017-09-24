from braintree import ErrorResult
import logging

from flask import g

from almanac.DAOs.braintree.merchant_dao import MerchantDAO
from almanac.DAOs.braintree.payments_dao import BraintreePaymentsDAO
from almanac.DAOs.event_dao import EventDAO
from almanac.DAOs.user_dao import UserDAO
from almanac.integrations.braintree.transactions import BraintreeTransactions
from almanac.models import EventTable, PaymentTable, db
from almanac.exc.exceptions import (
    FacadeException,
    DAOException,
)


class BraintreePaymentFacade(object):
    """
    Handles creating a new payment within braintree + our DB.
    """

    def issue_new_payment(self, event, nonce, address):
        """
        Issues a new payment w/in Braintree.

        :param EventTable event: The event that must be paid for.
        :param str nonce: The nonce which signifies which payment method
        is to be used.
        :param AddressTable address: The address information to be used
        whenever issuing a payment.
        :rtype: PaymentTable
        :return: The newly created payment.
        """
        try:
            submerchant = MerchantDAO().get_submerchant_by_id(
                event.scheduled_user_id
            )
        except DAOException as e:
            logging.error(
                'Invalid event ({0}) issued, no submerchant '
                '({1}). Exception of: {2}.'.format(
                    event.public_id,
                    event.scheduled_user_id,
                    e,
                )
            )
            raise DAOException(e)

        if submerchant is None:
            logging.error(
                'Failed to retrieve submerchant by public ID {0} for a new '
                'event.'.format(
                    event.scheduled_user_id
                )
            )
            raise FacadeException(
                'Invalid requested user. Contact support.'
            )

        try:
            # TODO(ian): This can be refactored to use
            # EventDAO().get_event_by_id and retrieve all the info in 1 query.
            new_transaction = BraintreeTransactions().create_transaction(
                submerchant,
                event.calculate_total_price(
                    event.duration,
                    UserDAO().get(event.scheduled_user_id),
                ),
                nonce,
                UserDAO().get(event.scheduling_user_id),
                address,
            )

            if isinstance(new_transaction, ErrorResult):
                logging.error(
                    'Received error result {0} when creating new '
                    'transaction for event {1}'.format(
                        new_transaction,
                        event
                    )
                )
                raise FacadeException('Failed to complete transaction.')

            return BraintreePaymentsDAO().insert_new_transaction(
                submerchant,
                event.total_price,
                event.calculate_service_fee(submerchant),
                event,
                skip_commit=True,
            )
        except Exception as e:
            db.session.rollback()
            logging.error(
                'Exception encountered while creating and inserting '
                'transaction: {0}.'.format(e),
            )
            raise FacadeException(e)
