import unittest
from unittest import mock

from almanac.exc.exceptions import IntegrationException
from almanac.integrations.braintree.customers import BraintreeCustomer
from almanac.models import db, UserTable as User
from almanac.almanac import create_app

app = create_app(None)


class TestCustomerIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_integration = BraintreeCustomer()

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

    def tearDown(self):
        with app.app_context():
            db.session.query(
                User
            ).delete()
            db.session.commit()

    @mock.patch('braintree.Customer.create')
    def test_create_customer(self, _mock):
        class __test:
            @property
            def is_success(self): return True

            @property
            def customer(self): return {}

        _mock.return_value = __test()

        with app.app_context():
            new_customer = self.test_integration.create_customer(
                'test_nonce',
                'test_customer_token',
                'first_name',
                'last_name',
                'user_id'
            )

            self.assertIsNotNone(new_customer)

    @mock.patch('braintree.Customer.create')
    def test_create_customer_fail(self, _mock):
        class __test:
            @property
            def is_success(self): return False
        _mock.return_value = __test()

        with app.app_context():
            with self.assertRaises(IntegrationException) as e:
                new_customer = self.test_integration.create_customer(
                    'test_nonce',
                    'test_customer_token',
                    'first_name',
                    'last_name',
                    'user_id'
                )

                self.assertEqual(e.msg, 'Failed to create payment method.')

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
