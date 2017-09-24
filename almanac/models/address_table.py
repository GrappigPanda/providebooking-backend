import logging

from almanac.DAOs.user_dao import UserDAO
from almanac.exc.exceptions import DAOException, TableException
from almanac.models import BaseTable
from almanac.models import db


class AddressTable(BaseTable):
    """
    Houses the schedules of contact form submissions.
    """
    __tablename__ = 'addresses'

    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        index=True
    )

    street_address = db.Column(db.String, nullable=False)
    extended_address = db.Column(db.String, nullable=True)
    # City
    locality = db.Column(db.String, nullable=False)
    # State
    region = db.Column(db.String, nullable=False)
    postal_code = db.Column(db.String, nullable=False)
    country_code_alpha2 = db.Column(db.String(2), nullable=False)

    is_default = db.Column(db.Boolean, nullable=False, default=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    # Indexes
    db.Index('idx_default_addresses', is_default)
    db.Index('idx_locality', locality)
    db.Index('idx_region', region)
    db.Index('idx_postal_code', postal_code)
    db.Index('idx_country_code', country_code_alpha2)

    def __init__(
            self,
            user_id,
            first_name,
            last_name,
            street_address,
            locality,
            region,
            postal_code,
            country_code_alpha2,
            is_default=False,
            extended_address=None
    ):
        super().__init__()
        try:
            self.user_id = UserDAO().get(user_id).id
        except DAOException as e:
            logging.error(
                'Failed to get user by pub ID {0} w/ exc of {1}'.format(
                    user_id,
                    e,
                )
            )
            raise TableException('Failed to find requested user.')
        except AttributeError as e:
            logging.error(
                'Requested user ({0}) does not exist when '
                'creating new address.'.format(
                    user_id,
                )
            )

            raise TableException(e)

        self.first_name = first_name
        self.last_name = last_name
        self.street_address = street_address
        self.locality = locality
        self.region = region
        self.postal_code = postal_code
        self.country_code_alpha2 = country_code_alpha2
        self.is_default = is_default

        if extended_address is not None and extended_address != '':
            self.extended_address = extended_address

    def __repr__(self):
        return """
            First name: {0} Last name: {1} Default: {2} Locality: {3}
            Region: {4} Country2: {5}
            """.format(
            self.first_name,
            self.last_name,
            self.is_default,
            self.locality,
            self.region,
            self.country_code_alpha2,
        )


