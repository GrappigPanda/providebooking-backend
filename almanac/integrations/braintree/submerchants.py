import braintree
import logging
from flask import current_app
from braintree import MerchantAccount, Transaction

from almanac.exc.exceptions import IntegrationException
from almanac.models.braintree.submerchant_table import SubmerchantTable

MINIMUM_AMOUNT_THRESHOLD = 15.0


class BraintreeSubmerchant(object):
    """
    Handles third-party integrations concerning submerchants for the braintree
    payment platform.
    """

    def create_submerchant(self, submerchant):
        """

        :param dict submerchant: The information to be used in creation of the
        submerchant.
        :rtype: dict
        :return: The submerchant's information
        """
        submerchant['funding']['destination'] = MerchantAccount.FundingDestination.Bank
        del submerchant['register_as_business']
        return braintree.MerchantAccount.create(submerchant)