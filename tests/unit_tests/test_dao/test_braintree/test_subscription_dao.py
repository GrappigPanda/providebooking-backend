import unittest

from almanac.DAOs.braintree.customer_dao import CustomerDAO
from almanac.DAOs.braintree.subscription_dao import SubscriptionDAO
from almanac.exc.exceptions import DAOException
from almanac.almanac import create_app
from almanac.models import (
    db,
    CustomerTable as Customer,
    UserTable as User,
    SubscriptionTable as Subscription,
)

app = create_app(None)


class TestSubscriptionDAOTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = SubscriptionDAO()

    def setUp(self):
        with app.app_context():
            test_user = User(
                'test-reset-16@email.com',
                'testpw',
                'US/Central',
                'test1',
            )

            test_user2 = User(
                'test-reset-17@email.com',
                'testpw',
                'US/Central',
                'test2',
            )

            self.test_uid = test_user.public_id
            self.test_uid2 = test_user2.public_id
            self.test_user_email = test_user.email

            db.session.add(test_user)
            db.session.add(test_user2)
            db.session.commit()

            test_customer = Customer(
                'test_customer_id',
                'cc_token',
                'first_name',
                'last_name',
                self.test_uid,
            )

            test_customer2 = Customer(
                'test_customer_id2',
                'cc_token2',
                'first_name',
                'last_name',
                self.test_uid2,
            )

            test_sub = Subscription(
                test_customer2.public_id,
                self.test_uid2,
                'UUID-id'
            )

            self.sub_id = test_sub.public_id

            db.session.add(test_customer)
            db.session.add(test_customer2)
            db.session.commit()

            db.session.add(test_sub)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.query(
                Subscription
            ).delete()

            db.session.query(
                Customer
            ).delete()

            db.session.query(
                User
            ).delete()

            db.session.commit()

    def test_get_subscription_by_public_id(self):
        with app.app_context():
            found_sub = self.test_dao.get_subscription_by_public_id(
                self.sub_id
            )

            self.assertIsNotNone(found_sub)

    def test_get_subscription_by_user_id(self):
        with app.app_context():
            found_sub = self.test_dao.get_subscription_by_user_id(
                self.test_uid2
            )

            self.assertIsNotNone(found_sub)

    def test_start_subscription(self):
        with app.app_context():
            new_subscription = self.test_dao.create_subscription(
                "bt_sub_id",
                self.test_uid,
            )

            self.assertIsNotNone(new_subscription)

    def test_cancel_subscription(self):
        with app.app_context():
            found_sub = self.test_dao.cancel_subscription(self.test_uid2)

            self.assertIsNotNone(found_sub)

    def test_cancel_subscription_fail_sub_not_exists(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                found_sub = self.test_dao.cancel_subscription('INVALID')

                self.assertIsNotNone(found_sub)
                self.assertEqual(e.msg, 'Failed to cancel subscription.')

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
