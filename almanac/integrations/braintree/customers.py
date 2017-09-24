import braintree
import logging
from flask import current_app
from braintree import MerchantAccount, Transaction

from almanac.exc.exceptions import IntegrationException
from almanac.models.braintree.submerchant_table import SubmerchantTable

MINIMUM_AMOUNT_THRESHOLD = 15.0


class BraintreeCustomer(object):
    """
    Handles third-party integrations concerning customers for the braintree
    payment platform.
    """

    def create_customer(self, nonce, customer_token, first_name, last_name,
                        user_id, *, make_default=False):
        """
        Handles creating a customer account with a unique identifier and a
        payment method.

        :param str nonce: A nonce identifying a card -- created by BT
        hosted fields on the FE.
        :param str customer_token: The customer's unique token (used in our
        DB) to reference a payment method.
        :param str first_name: The customer's first name.
        :param str last_name: The customer's last name.
        :param str user_id: The user's unique UUID.
        :param bool make_default: If a user specifies to make this their
        default payment method, we want to assign that value.
        :rtype: braintree.Customer
        :return: The newly created customer.
        """
        new_customer = braintree.Customer.create({
            'first_name': first_name,
            'last_name': last_name,
            'payment_method_nonce': nonce,
            'credit_card': {
                'token': customer_token,
                'options': {
                    'make_default': make_default,
                    'verify_card': True,
                },
            },
            'custom_fields': {
                'app_user_id': str(user_id),
            },
        })

        if not new_customer.is_success:
            logging.error(
                'Failed to create payment method for {0} '
                'with exception.'.format(
                    user_id,
                )
            )
            raise IntegrationException('Failed to create payment method.')

        return new_customer.customer

