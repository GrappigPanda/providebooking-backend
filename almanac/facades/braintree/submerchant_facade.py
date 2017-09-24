import logging

import shortuuid

from almanac.DAOs.braintree.merchant_dao import MerchantDAO
from almanac.DAOs.user_dao import UserDAO
from almanac.exc.exceptions import FacadeException, DAOException
from almanac.integrations.braintree.submerchants import BraintreeSubmerchant


class SubmerchantFacade(object):
    """
    Acts as a facade to handle complete Braintree integration.
    """

    def create_submerchant(self, submerchant_info, user_id, *,
                           skip_commit=False):
        """
        Handles creation of the submerchant.

        :param dict submerchant_info: The information to be used in
        submerchant creation.
        :param str user_id: The user's UUID.
        :param bool skip_commit: Handles skipping commit if desired.
        :rtype: dict
        :return: The submerchant's info.
        """
        self._assert_no_duplicate_submerchant(user_id)
        merchant_dao = MerchantDAO()

        account_id = self._make_account_id()
        master_account_id = merchant_dao.get_master_merchant().account_id
        submerchant_info['master_merchant_account_id'] = master_account_id
        submerchant_info['id'] = self._make_account_id()
        register_as_business = submerchant_info['register_as_business']

        result = BraintreeSubmerchant().create_submerchant(submerchant_info)

        if not result.is_success:
            logging.info(
                'Failed to create submerchant under master merchant {0} '
                '-- {1} error: {2}'.format(
                    account_id,
                    submerchant_info,
                    result
                )
            )
            raise FacadeException(
                'Failed to create submerchant. {0}'.format(result)
            )

        merchant_dao.create_submerchant(
            submerchant_info,
            register_as_business,
            user_id,
            skip_commit=skip_commit
        )

        return submerchant_info

    def _assert_no_duplicate_submerchant(self, user_id):
        """
        Handles asserting that a user doesn't already have a submerchant.

        :param str user_id: The user's UUID
        :raises: FacadeException
        """
        try:
            UserDAO().get(user_id)
        except DAOException as e:
            logging.warning(
                'Requested user {0} does not exist with exception: {1}'.format(
                    user_id,
                    e,
                )
            )
            raise FacadeException('Requested user does not exist.')

        merchant_dao = MerchantDAO()
        found_submerchant = merchant_dao.get_submerchant_by_id(user_id)
        if found_submerchant is not None:
            logging.warning(
                'Attempted duplicate submerchant for user: {0}'.format(
                    user_id,
                )
            )
            raise FacadeException(
                'You already have a submerchant account created.'
            )

    def _make_account_id(self):
        """
        Handles creation of the account ID. Just a simple tagging system.

        :rtype: string
        :return: A UUID (converted to a string) which will be the unique
        identifier.
        """
        return shortuuid.uuid()
