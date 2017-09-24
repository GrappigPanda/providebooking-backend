import logging
import uuid

import shortuuid

from almanac.DAOs.braintree.customer_dao import CustomerDAO
from almanac.integrations.braintree.customers import BraintreeCustomer


class CustomerFacade(object):
    """
    Acts as a facade to handle Braintree customers.
    """
    def __init__(self):
        self.customer_dao = CustomerDAO()
        self.customer_integration = BraintreeCustomer()

    def create_customer(self, nonce, first_name, last_name, user_id, *,
                        make_default=False, skip_commit=False):
        """
        Handles creating a customer account with a unique identifier and a
        payment method.

        :param str nonce: A nonce identifying a card -- created by BT
        hosted fields on the FE.
        :param str first_name: The customer's first name.
        :param str last_name: The customer's last name.
        :param str user_id: The user's unique UUID.
        :param bool make_default: If a user specifies to make this their
        default payment method, we want to assign that value.
        :param bool skip_commit: Should we skip committing? Facades on facades
        :rtype: CustomerTable
        :return: The newly created customer.
        """
        customer_token = str(uuid.uuid4())

        new_customer = self.customer_integration.create_customer(
            nonce,
            customer_token,
            first_name,
            last_name,
            user_id,
            make_default=make_default
        )

        return self.customer_dao.create_customer(
            "bt_customer_id",
            "cc_token",
            first_name,
            last_name,
            user_id,
            skip_commit=skip_commit,
        )

    def delete_customer(self):
        pass