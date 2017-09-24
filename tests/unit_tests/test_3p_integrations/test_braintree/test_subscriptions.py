import unittest
from unittest import mock

from almanac.exc.exceptions import IntegrationException
from almanac.integrations.braintree.subscriptions import BraintreeSubscription
from almanac.models import (
    db,
    UserTable as User,
    CustomerTable as Customer
)
from almanac.almanac import create_app

app = create_app(None)


class SubscriptionFacadeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_integration = BraintreeSubscription()

    def setUp(self):
        with app.app_context():
            test_user = User(
                'test-reset@email.com',
                'testpw',
                'US/Central',
                'test6',
            )

            self.test_uid = test_user.public_id
            self.test_user_email = test_user.email

            db.session.add(test_user)
            db.session.commit()

            # TODO(ian): Create a mock customer/payment method

    def tearDown(self):
        with app.app_context():
            db.session.query(
                User
            ).delete()

            db.session.query(
                Customer
            ).delete()

            db.session.commit()

    @mock.patch('braintree.Subscription.create')
    def test_start_subscription(self, _mock):
        class __test:
            @property
            def is_success(self): return True

            @property
            def customer(self): return {}

        _mock.return_value = __test()

        with app.app_context():
            pass

    @mock.patch('braintree.Subscription.create')
    def test_start_subscription_fail_invalid_payment_method(self, _mock):
        class __test:
            @property
            def is_success(self): return False

            @property
            def customer(self): return {}

        _mock.return_value = __test()

        with app.app_context():
            pass

    @mock.patch('braintree.Subscription.create')
    def test_cancel_subscription(self, _mock):
        class __test:
            @property
            def is_success(self): return True

            @property
            def customer(self): return {}

        _mock.return_value = __test()

        with app.app_context():
            pass

    @mock.patch('braintree.Subscription.create')
    def test_cancel_subscription_fail_subscription_id_not_found(self, _mock):
        class __test:
            @property
            def is_success(self): return False

            @property
            def customer(self): return {}

        _mock.return_value = __test()

        with app.app_context():
            pass

    @mock.patch('braintree.Subscription.create')
    def test_cancel_subscription_fail_unknown(self, _mock_sub):
        class __test:
            @property
            def is_success(self): return False

            @property
            def customer(self): return {}

        _mock_sub.return_value = __test()

        with app.app_context():
            pass

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
