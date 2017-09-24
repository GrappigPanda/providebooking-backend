from datetime import datetime

from almanac.models.base_table import BaseTable
from almanac.models import db


class SubscriptionTable(BaseTable):
    """
    Houses storing information about a customer account.
    """
    __tablename__ = 'braintree_subscription'

    braintree_sub_id = db.Column(db.String, nullable=False)
    plan_id = db.Column(db.String, nullable=False, default='Basic0x01')
    date_started = db.Column(db.DateTime, nullable=False)
    date_ended = db.Column(db.DateTime, nullable=True)

    user_id = db.Column(
        db.String(36),
        db.ForeignKey('users.public_id'),
        nullable=False,
    )

    braintree_customer_id = db.Column(
        db.String(36),
        db.ForeignKey('braintree_customer.public_id'),
        nullable=False,
    )

    # House keeping stuff.
    is_deleted = db.Column(db.BOOLEAN, nullable=False, default=False)

    def __init__(self, bt_customer_id, user_id, sub_id, *,
                 plan_id='Basic0x01'):
        super().__init__()

        self.braintree_customer_id = bt_customer_id
        self.braintree_sub_id = sub_id
        self.user_id = user_id
        self.plan_id = plan_id
        self.date_started = datetime.utcnow()

    def __repr__(self):
        return 'User: {0} -- PlanID: {1} -- CustomerID: {2}'.format(
            self.user_id,
            self.plan_id,
            self.braintree_customer_id,
        )

