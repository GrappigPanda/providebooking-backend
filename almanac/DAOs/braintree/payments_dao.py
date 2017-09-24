import logging
from flask import current_app

from almanac.DAOs.base_dao import BaseDAO
from almanac.models import db
from almanac.models import SubmerchantTable, PaymentTable
from almanac.utils.database_utils import exec_and_commit


class BraintreePaymentsDAO(BaseDAO):
    """
    Handles payments.
    """

    def insert_new_transaction(
            self,
            submerchant,
            amount,
            service_fee,
            event,
            *,
            skip_commit=False
    ):
        """
        Handles logging a new transaction

        :param SubmerchantTable submerchant:
        :param Float amount: The total amount for booked time.
        :param Float service_fee: The service fee being added onto the
        transaction.
        :param EventTable event: The event that is being booked.
        :param bool skip_commit: Tells if we should add, but not commit yet.
        :rtype: PaymentTable
        :return: The newly created payment row.
        """
        new_payment = PaymentTable(
            amount,
            service_fee,
            submerchant,
            event,
        )

        try:
            exec_and_commit(
                db.session.add,
                new_payment,
                skip_commit=skip_commit,
            )
        except Exception as e:
            logging.critical(
                'Failed to log payment {0} with exception of {1}'.format(
                    new_payment,
                    e
                )
            )

        return new_payment
