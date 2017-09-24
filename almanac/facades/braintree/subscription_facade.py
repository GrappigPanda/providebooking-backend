import logging
import uuid
from uuid import UUID

from almanac.DAOs.braintree.customer_dao import CustomerDAO
from almanac.DAOs.braintree.subscription_dao import SubscriptionDAO
from almanac.DAOs.user_dao import UserDAO
from almanac.exc.exceptions import FacadeException, DAOException
from almanac.facades.braintree.customer_facade import CustomerFacade
from almanac.integrations.braintree.subscriptions import BraintreeSubscription
from almanac.models import db, CustomerTable


class SubscriptionFacade(object):
    """
    Acts as a facade to handle Braintree submerchants.
    """
    def __init__(self):
        self.customer_facade = CustomerFacade()
        self.customer_dao = CustomerDAO()
        self.subscription_integration = BraintreeSubscription()
        self.user_dao = UserDAO()
        self.subscription_dao = SubscriptionDAO()

    def create_new_subscription_with_customer(
            self, user_id, nonce, first_name, last_name,
            *, skip_commit=True, plan_id='Basic0x01'):
        """
        Handles creating a new customer with a new subscription.

        :param str user_id: The user to create the customer and subscription
        for.
        :param str nonce: A nonce identifying a card -- created by BT
        hosted fields on the FE.
        :param str first_name: The user's first name.
        :param str last_name: The user's last name.
        :param bool skip_commit: Should we skip committing? Facades on facades
        :param str plan_id: The plan ID. Don't touch!
        :rtype: SubscriptionTable
        :return: The newly created subscription.
        """
        found_customer = self._customer_exists(user_id)
        if found_customer:
            return self.create_new_subscription(
                user_id,
                skip_commit=skip_commit,
                plan_id=plan_id,
            )

        try:
            # type: CustomerTable
            new_customer = self.customer_facade.create_customer(
                nonce,
                first_name,
                last_name,
                user_id,
                skip_commit=skip_commit
            )

            sub_id = uuid.uuid4()

            new_subscription = self.subscription_integration.start_subscription(
                sub_id,
                new_customer.credit_card_token,
                plan_id,
            )

            self.subscription_dao.create_subscription(
                sub_id,
                user_id,
                skip_commit=skip_commit,
            )

            db.session.commit()

            return new_subscription
        except Exception as e:
            logging.error(
                'Failed to create new customer for user {0} with '
                'exception {1}'.format(
                    user_id,
                    e,
                )
            )
            db.session.rollback()
            raise FacadeException(
                'Failed to start subscription.'
            )

    def cancel_subscription(self, user_id, *, skip_commit=False):
        """
        Handles cancelling the currently running subscription for the user

        :param str user_id: The user to cancel the subscription for.
        :param bool skip_commit: Should we skip committing? Facades on facades
        :rtype: CustomerTable
        :return: The newly created customer.
        """
        return self.subscription_dao.cancel_subscription(
            user_id,
        )

    def create_new_subscription(self, user_id, *,
                                skip_commit=False, plan_id='Basic0x01'):
        """
        Handles creating a new subscription for an existing customer account.

        :param str user_id: The user to create the subscription for.
        :param bool skip_commit: Should we skip committing? Facades on facades
        :param str plan_id: The plan ID. Don't touch!
        :rtype: SubscriptionTable
        :return: The newly created subscription.
        """
        try:
            found_customer = self.customer_dao.get_customer_by_user_id(user_id)

            unique_id = uuid.uuid4()

            new_subscription = self.subscription_integration.start_subscription(
                unique_id,
                found_customer.credit_card_token,
                plan_id,
            )

            self.subscription_dao.create_subscription(
                unique_id,
                user_id,
                skip_commit=skip_commit,
            )

            db.session.commit()

            return new_subscription
        except Exception as e:
            logging.error(
                'Failed to create new subscription for user {0} with '
                'exception {1} for pre-existing customer.'.format(
                    user_id,
                    e,
                )
            )
            db.session.rollback()
            raise FacadeException(
                'Failed to start subscription.'
            )

    def _customer_exists(self, user_id):
        try:
            return self.customer_dao.get_customer_by_user_id(user_id)
        except DAOException as e:
            return False
