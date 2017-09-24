from almanac.models import BaseTable
from almanac.models import db


class PaymentTable(BaseTable):
    """
    Houses storing information pertinent to the master merchant.
    """
    __tablename__ = 'payments'

    submerchant_id = db.Column(
        db.Integer,
        db.ForeignKey('braintree_sub_merchant.id')
    )

    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.id')
    )

    base_amount = db.Column(db.DECIMAL, nullable=False)
    service_fee = db.Column(db.DECIMAL, nullable=False)
    total_price = db.Column(db.DECIMAL, nullable=False)

    def __init__(self, amount, service_fee, submerchant, event):
        super().__init__()

        self.base_amount = amount
        self.service_fee = service_fee
        self.total_price = event.total_price

        self.submerchant_id = submerchant.public_id
        self.event_id = event.public_id

    def __repr__(self):
        return 'Transaction {0} for submerchant {1} and event {2}'.format(
            self.public_id,
            self.submerchant_id,
            self.event_id
        )
