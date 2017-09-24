import logging
from http import HTTPStatus

from almanac.DAOs.base_dao import BaseDAO
from almanac.DAOs.user_dao import UserDAO
from almanac.exc.exceptions import DAOException
from almanac.models import db
from almanac.models import AddressTable as Address, UserTable as User
from almanac.utils.database_utils import exec_and_commit


class AddressDAO(BaseDAO):
    """
    Handles addresses.
    """

    def get_by_public_id(self, public_id, user_public_id):
        """
        Retrieves a single address by its public ID.

        :param str public_id: The UUID associated with an address.
        :param str user_public_id: The user's public ID.
        :rtype: AddressTable
        :return: A single address object.
        """
        address = db.session.query(
            Address
        ).filter_by(
            public_id=public_id,
            is_deleted=False,
        ).join(
            User
        ).filter_by(
            public_id=user_public_id
        ).first()

        if address is None:
            logging.error(
                'Failed to find requested address {0} for user {1}'.format(
                    public_id,
                    user_public_id
                )
            )
            raise DAOException(
                'Failed to find requested address.',
                HTTPStatus.NOT_FOUND
            )

        return address

    def get_all_addresses_for_user(self, user_public_id):
        """
        Retrieves all of the addresses for a user.

        :param str user_public_id: The user's public ID.
        :rtype: List[Address]
        :return: All available addresses for a user.
        """
        return db.session.query(
            Address
        ).filter_by(
            is_deleted=False,
        ).join(
            User
        ).filter_by(
            public_id=user_public_id
        ).all()

    def get_default_for_user(self, user_public_id):
        """
        Retrieves the default address for a user.

        :param str user_public_id: The user's public ID.
        :rtype: Address
        :return: The default address associated with a user.
        """
        address = db.session.query(
            Address
        ).filter_by(
            is_deleted=False,
            is_default=True,
        ).join(
            User
        ).filter_by(
            public_id=user_public_id
        ).first()

        if address is None:
            logging.error(
                'Failed to find default address for user {0}'.format(
                    user_public_id
                )
            )
            raise DAOException(
                'Failed to find default address.',
                HTTPStatus.NOT_FOUND
            )

        return address

    def create_address(
            self,
            user_public_id,
            first_name,
            last_name,
            street_address,
            locality,
            region,
            postal_code,
            country_code_alpha2,
            is_default=False,
            extended_address=None,
            *,
            skip_commit=False
    ):
        """
        Handles creation of a new address.

        :param str user_public_id: The user's public ID.
        :param str first_name: The user's first name.
        :param str last_name: The user's last name.
        :param str street_address: The first part of the address. The meat of
        it.
        :param str locality: The locality. Might be a city or town.
        :param str region: The region. Typically things like states (in the US)
        :param str postal_code: The postal code associated with the address.
        :param str country_code_alpha2: The country code. ('US', 'CA', 'MX')
        :param bool is_default: Set this to default on creation?
        :param str extended_address: (Default: None) The second part of the
        address. Typically things like apartment # etc.
        :param bool skip_commit: An optional flag used to indicate if we want
        to create the object and add to DB delta, but not commit it just yet.
        Used mostly for facade methods which roll back if the event doesn't
        fully complete (transaction doesn't finalize, &c.).
        :rtype: AddressTable
        :return: The newly created address.
        """
        new_address = Address(
            user_public_id,
            first_name,
            last_name,
            street_address,
            locality,
            region,
            postal_code,
            country_code_alpha2,
            is_default,
            extended_address,
        )

        if is_default:
            self._unset_default_address(user_public_id)

        exec_and_commit(db.session.add, new_address, skip_commit=skip_commit)

        return new_address

    def update_address(self, address_id, user_public_id, **args):
        """
        Handles updating any fields within the address

        :return:
        """
        address = self.get_by_public_id(address_id, user_public_id)

        to_update = {}
        for k, v in args.items():
            to_update[k] = v

        user = UserDAO().get(user_public_id)

        if len(to_update.keys()) > 0:
            db.session.query(
                Address
            ).filter_by(
                is_deleted=False,
                public_id=address_id,
                user_id=user.id,
            ).update(
                to_update
            )
            db.session.commit()

        return address

    def delete_address(self, address_id, user_public_id):
        """
        Handles soft deleting an address.

        :param str address_id: The address to delete.
        :param str user_public_id: The user to delete the address for.
        :rtype: Address
        :return: The address recently deleted.
        """
        address = self.get_by_public_id(address_id, user_public_id)

        address.is_deleted = True
        address.is_default = False

        db.session.commit()

        return address

    def _unset_default_address(self, user_public_id):
        """
        Removes the default address (not deletion, but makes it no longer
        default).

        :param str user_public_id: The user's public ID.
        :rtype: AddressTable
        :return: The address which was previously default.
        """
        found_row = self.get_default_for_user(user_public_id)

        found_row.is_default = False
        db.session.commit()

