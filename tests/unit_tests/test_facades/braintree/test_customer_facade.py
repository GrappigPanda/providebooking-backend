import unittest
from unittest import mock

from almanac.almanac import app
from almanac.exc.exceptions import IntegrationException
from almanac.facades.braintree.customer_facade import CustomerFacade
from almanac.models import db, CustomerTable as Customer
from almanac.models import UserTable as User


class CustomerFacadeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_facade = CustomerFacade()

            test_user = User(
                "test@email.com",
                "testpw",
                'US/Central',
                'test1',
            )

            cls.test_uid = test_user.public_id

            db.session.add(test_user)
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
            new_customer = self.test_facade.create_customer(
                'test-nonce',
                'first_name',
                'last_name',
                self.test_uid,
                make_default=True,
                skip_commit=False
            )

            self.assertIsNotNone(new_customer)

            retval = db.session.query(
                Customer
            ).filter_by(
                public_id=new_customer.public_id,
            ).first()

            self.assertIsNotNone(retval)

    @mock.patch('braintree.Customer.create')
    def test_create_customer_fail(self, _mock):
        class __test:
            @property
            def is_success(self): return False
        _mock.return_value = __test()
        with app.app_context():
            with self.assertRaises(IntegrationException) as e:
                self.test_facade.create_customer(
                    'test_nonce',
                    'first_name',
                    'last_name',
                    'user_id'
                )

                self.assertEqual(e.msg, 'Failed to create payment method.')

                retval = db.session.query(
                    Customer
                ).filter_by(
                    user_id='user_id',
                ).first()

                self.assertIsNone(retval)

