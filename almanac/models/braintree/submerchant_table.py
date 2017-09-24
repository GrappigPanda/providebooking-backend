from almanac.models import BaseTable
from almanac.models import db


class SubmerchantTable(BaseTable):
    """
    Houses storing information relevant for submerchants.
    """
    __tablename__ = 'braintree_sub_merchant'

    master_merchant_id = db.Column(
        db.Integer,
        db.ForeignKey('braintree_master_merchant.id')
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.public_id'),
        nullable=False,
    )

    # House keeping stuff.
    is_deleted = db.Column(db.BOOLEAN, nullable=False, default=False)
    is_approved = db.Column(db.BOOLEAN, nullable=False, default=False)
    is_rejected = db.Column(db.Boolean, nullable=False, default=False)

    # Actual shit being put into braintree upon submerchant account creation.
    braintree_account_id = db.Column(db.String(24), nullable=False)

    service_fee_percent = db.Column(db.DECIMAL, nullable=False, default=.025)

    # Individual
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    date_of_birth = db.Column(db.DateTime, nullable=False)
    address_street_address = db.Column(db.String(128), nullable=False)
    address_locality = db.Column(db.String(32), nullable=False)
    address_region = db.Column(db.String(32), nullable=False)
    address_zip = db.Column(db.String(12), nullable=False)

    # Business stuff. Only required if user is registering as a business
    register_as_business = db.Column(db.Boolean, nullable=False, default=False)
    legal_name = db.Column(db.String(64))
    # NOTE: We do NOT store the tax_id.
    dba_name = db.Column(db.String(64))
    bus_address_street_address = db.Column(db.String(128))
    bus_address_locality = db.Column(db.String(32))
    bus_address_region = db.Column(db.String(32))
    bus_address_zip = db.Column(db.String(12))

    def __init__(self,
                 user_id,
                 account_id,
                 first_name,
                 last_name,
                 email,
                 date_of_birth,
                 address_street_address,
                 address_locality,
                 address_region,
                 address_zip,
                 register_as_business=False,
                 legal_name=None,
                 dba_name=None,
                 bus_address_street_address=None,
                 bus_address_locality=None,
                 bus_address_region=None,
                 bus_address_zip=None):
        super().__init__()

        self.user_id = user_id

        self.braintree_account_id = account_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.date_of_birth = date_of_birth
        self.address_street_address = address_street_address
        self.address_locality = address_locality
        self.address_region = address_region
        self.address_zip = address_zip

        if register_as_business:
            self.register_as_business = register_as_business
            self.legal_name = legal_name
            self.dba_name = dba_name
            self.bus_address_street_address = bus_address_street_address
            self.bus_address_locality = bus_address_locality
            self.bus_address_region = bus_address_region
            self.bus_address_zip = bus_address_zip

    def __repr__(self):
        return 'Account ID: {0} -- User Public ID: {1}'.format(
            self.braintree_account_id,
            self.user_id
        )
