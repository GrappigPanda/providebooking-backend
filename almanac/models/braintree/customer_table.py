from almanac.models.base_table import BaseTable
from almanac.models import db


class CustomerTable(BaseTable):
    """
    Houses storing information about a customer account.
    """
    __tablename__ = 'braintree_customer'

    braintree_customer_id = db.Column(db.String, nullable=False, unique=True)
    credit_card_token = db.Column(db.String, nullable=False, unique=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)

    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.public_id'),
        nullable=False,
    )

    # House keeping stuff.
    is_default = db.Column(db.BOOLEAN, nullable=False, default=False)
    is_deleted = db.Column(db.BOOLEAN, nullable=False, default=False)

    def __init__(self, bt_customer_id, cc_token, first_name, last_name,
                 user_id, *, is_default=False):
        super().__init__()

        self.braintree_customer_id = bt_customer_id
        self.credit_card_token = cc_token
        self.first_name = first_name
        self.last_name = last_name
        self.user_id = user_id
        self.is_default = is_default

    def __repr__(self):
        return 'User: {0} -- Default: {1} -- CustomerID: {2}'.format(
            self.user_id,
            self.is_default,
            self.braintree_customer_id,
        )

