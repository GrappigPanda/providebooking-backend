import logging

from braintree import WebhookNotification
from flask import current_app

from almanac.DAOs.base_dao import BaseDAO
from almanac.exc.exceptions import DAOException
from almanac.models import db
from almanac.models import MasterMerchantTable as MasterMerchant
from almanac.models import SubmerchantTable as SubMerchant
from almanac.utils.database_utils import exec_and_commit


class MerchantDAO(BaseDAO):
    """
    Handles merchant shit.
    """

    def get_master_merchant(self):
        """
        Handles retrieving the master merchant account.

        :rtype: MasterMerchantTable
        :return: The master merchant info.
        """
        retval = db.session.query(MasterMerchant).filter_by(
            environment=current_app.config.get('ENVIRONMENT', 'dev').upper()
        ).first()

        if retval is None:
            raise DAOException('Requested merchant account does not exist.')

        return retval

    def create_submerchant(self,
                           submerchant_info,
                           register_as_business,
                           user_id,
                           *,
                           skip_commit=False
                           ):
        """
        Handles adding the submerchant into the database for tracking purposes.

        :param dict submerchant_info: The information to be used in
        submerchant creation.
        :param bool register_as_business: Boolean indiicating if registering
        as a individual (false) or as a business (True).
        :param bool skip_commit: An optional flag used to indicate if we want
        to create the object and add to DB delta, but not commit it just yet.
        Used mostly for facade methods which roll back if the event doesn't
        fully complete (transaction doesn't finalize, &c.).
        :rtype: dict
        :return: The submerchant's info.
        """

        new_submerchant = SubMerchant(
            user_id,
            submerchant_info['id'],
            submerchant_info['individual']['first_name'],
            submerchant_info['individual']['last_name'],
            submerchant_info['individual']['email'],
            submerchant_info['individual']['date_of_birth'],
            submerchant_info['individual']['address']['street_address'],
            submerchant_info['individual']['address']['locality'],
            submerchant_info['individual']['address']['region'],
            submerchant_info['individual']['address']['postal_code'],
        )

        if register_as_business:
            new_submerchant.legal_name = submerchant_info['business']['legal_name']
            new_submerchant.dba_name = submerchant_info['business']['dba_name']
            new_submerchant.bus_address_street_address = submerchant_info['business']['address']['street_address']
            new_submerchant.bus_address_locality = submerchant_info['business']['address']['locality']
            new_submerchant.bus_address_region = submerchant_info['business']['address']['region']
            new_submerchant.bus_address_zip = submerchant_info['business']['address']['postal_code']

        exec_and_commit(
            db.session.add,
            new_submerchant,
            skip_commit=skip_commit
        )

        return submerchant_info

    def get_submerchant_by_id(self, submerchant_public_id):
        """
        Retrieves the submerchant from the DB by it's public ID.

        :param str submerchant_public_id: The submerchan'ts public UUID
        :rtype: SubmerchantTable
        :return: The submerchant.
        """
        try:
            return db.session.query(
                SubMerchant
            ).filter_by(
                user_id=submerchant_public_id,
            ).first()
        except Exception as e:
            logging.error(
                'Failed to query submerchant w/ public ID {0} '
                'w/ exc of {1}'.format(
                    submerchant_public_id,
                    e
                )
            )
            raise DAOException(
                'No submerchant found with that id.'
            )

    def set_approved_or_declined(self, notify):
        """
        Handles updating a submerchant and setting them as approved or denied.

        :param WebhookNotification notify: The parsed notifcation received
        from an endpoint
        """
        if notify.kind == WebhookNotification.Kind.SubMerchantAccountApproved:
            db.session.query(
                SubMerchant
            ).filter_by(
                braintree_account_id=notify.merchant_account.id,
            ).update({
                'is_approved': True,
                'is_rejected': False,
            })
            db.session.commit()
        else:
            db.session.query(
                SubMerchant
            ).filter_by(
                braintree_account_id=notify.merchant_account.id,
            ).update({
                'is_rejected': True,
                'is_approved': False,
            })
            db.session.commit()
