import uuid
import bcrypt
import pytz

from almanac.exc.exceptions import ModelException, SQLException
from almanac.models import SubmerchantTable
from almanac.models import db, BaseTable


class UserTable(BaseTable):
    """
    Houses the DB definition of the users table.
    """
    __tablename__ = 'users'

    email = db.Column(db.String, nullable=False, unique=True)
    username = db.Column(db.String(32), nullable=False, unique=True)
    password = db.Column(db.Binary(64), nullable=False)

    # House keeping stuff.
    is_deleted = db.Column(db.BOOLEAN, nullable=False)

    # user info
    local_tz = db.Column(db.String(32), nullable=False)

    # Schedule and event stuff.
    is_premium = db.Column(db.BOOLEAN, nullable=False, default=False)
    five_min_price = db.Column(db.DECIMAL, nullable=True)
    fifteen_min_price = db.Column(db.DECIMAL, nullable=True)
    thirty_min_price = db.Column(db.DECIMAL, nullable=True)
    sixty_min_price = db.Column(db.DECIMAL, nullable=True)

    verify_token = db.Column(
        db.String(36),
        unique=True,
        nullable=True,
        index=True
    )

    reset_token = db.Column(
        db.String(36),
        unique=True,
        nullable=True,
        index=True
    )

    is_validated = db.Column(db.BOOLEAN, nullable=False, default=False)

    def compare_password(self, plaintext_password):
        """
        Compares a user-input password to the stored hash.

        :param str plaintext_password: The password that the user put in.
        :rtype: bool
        :return: True if valid password--False otherwise.
        """
        if isinstance(self.password, bytes):
            return bcrypt.checkpw(
                plaintext_password.encode('utf-8'),
                self.password.decode('utf-8').encode('utf-8')
            )
        else:
            return bcrypt.checkpw(
                plaintext_password.encode('utf-8'),
                self.password.encode('utf-8')
            )

    def __init__(self, email, plaintext_password, local_tz, username):
        super().__init__()
        self.email = email
        self.is_deleted = False
        self.password = self._bcrypt_password(plaintext_password)
        self.username = username

        if local_tz in pytz.all_timezones:
            self.local_tz = local_tz
        else:
            raise ModelException('Invalid selected timezone: {0}'.format(
                local_tz
            ))

        self.verify_token = str(uuid.uuid4())

    def __repr__(self):
        return "Email: {0} - Deleted: {1} - GUID: {2}".format(
            self.email,
            self.is_deleted,
            self.public_id
        )

    @staticmethod
    def _bcrypt_password(plaintext_password, work_factor=10):
        """
        Bcrypt hashes a password

        :param str plaintext_password: The password to hash.
        :rtype: str
        :return: The bcrypt hash of the password.
        """
        return bcrypt.hashpw(
            plaintext_password.encode('utf-8'),
            bcrypt.gensalt(work_factor, b'2b')
        )

    @staticmethod
    def _bcrypt_compare(plaintext, stored_password):
        """
        Handles comparing a password to the stored password.

        :param str plaintext:
        :param str stored_password: The password currently stored for the user.
        :return:
        """
        return bcrypt.checkpw(plaintext.encode('utf-8'), stored_password)

    def __add__(self, submerchant):
        if not isinstance(submerchant, SubmerchantTable):
            raise SQLException('Invalid submerchant passed in: {0}'.format(
                submerchant
            ))

        self.has_deposit_account = True
        self.is_approved = submerchant.is_approved
        self.is_rejected = submerchant.is_rejected
        self.service_fee_percent = submerchant.service_fee_percent

        return self
