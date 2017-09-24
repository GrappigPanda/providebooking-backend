from almanac.models.base_table import BaseTable
from almanac.models import db


class MasterMerchantTable(BaseTable):
    """
    Houses storing information pertinent to the master merchant.
    """
    __tablename__ = 'braintree_master_merchant'

    account_id = db.Column(db.String, nullable=False, unique=True)
    environment = db.Column(db.String, nullable=False, default='DEV')

    def __init__(self, account_id):
        super().__init__()

        self.account_id = account_id

    def __repr__(self):
        return 'Account ID: {0} -- Environment: {1}'.format(
            self.account_id,
            self.environment
        )
