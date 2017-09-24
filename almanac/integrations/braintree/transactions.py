import logging
from braintree import Transaction

from almanac.exc.exceptions import IntegrationException
from almanac.models.braintree.submerchant_table import SubmerchantTable

MINIMUM_AMOUNT_THRESHOLD = 15.0


class BraintreeTransactions(object):
    """
    Handles third-party integrations with the braintree payment platform.
    """
    def create_transaction(
            self,
            submerchant,
            amount,
            nonce,
            billed_user,
            address,
    ):
        """
        Handles creating a transaction.

        :param SubmerchantTable submerchant: The submerchant who receives the
        lion's share
        :param float amount: The amount to be charged from the requesting user.
        :param str nonce: The payment nonce which is used to determine the
        method of payment for the customer.
        :param AddressTable address: The address used for billing.
        :param UserTable billed_user: The user who is being charged.
        :raises: IntegrationException
        :rtype: Transaction
        :return: The newly created transaction
        """
        if amount < MINIMUM_AMOUNT_THRESHOLD:
            raise IntegrationException(
                'Invalid amount requested. Minimum amount accepted is 15'
            )

        try:
            return Transaction.sale({
                'merchant_account_id': submerchant.braintree_account_id,
                'payment_method_nonce': nonce,
                'amount': amount,
                'service_fee_amount': self._calculate_service_fee(
                    amount,
                    submerchant
                ),
                'billing': {
                    address.first_name,
                    address.last_name,
                    address.street_address,
                    address.extended_address,
                    address.locality,
                    address.region,
                    address.postal_code,
                    address.country_code_alpha2,
                }
            })
        except Exception as e:
            logging.error(
                'Failed to create new transaction with '
                'exception of {0}. For submerchant {1} in amount {2}'.format(
                    e,
                    submerchant,
                    amount
                )
            )
            raise IntegrationException('Failed to create transaction.')

    # TODO(ian): Refactor this to use event_table's implementation.
    def _calculate_service_fee(self, amount, submerchant):
        try:
            return amount * submerchant.service_fee_percent
        except Exception as e:
            logging.critical(
                'Failed to `_calculate_service_fee` with exc: '
                '{0} for submerchant {1}'.format(
                    e,
                    submerchant.public_id
                )
            )

            return 1.0