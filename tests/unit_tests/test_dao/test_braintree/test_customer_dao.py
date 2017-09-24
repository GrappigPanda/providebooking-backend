import unittest

from almanac.DAOs.braintree.customer_dao import CustomerDAO
from almanac.exc.exceptions import DAOException
from almanac.models import db, CustomerTable as Customer, UserTable as User
from almanac.almanac import create_app

app = create_app(None)


class TestCustomerDAOTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = CustomerDAO()

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
                Customer
            ).delete()
            db.session.query(
                User
            ).delete()
            db.session.commit()

    def test_get_customer_by_user_id(self):
        with app.app_context():
            new_customer = self.test_dao.create_customer(
                'bt_customer_id',
                'cc_token',
                'first_name',
                'last_name',
                self.test_uid,
                is_default=True,
            )

            self.assertIsNotNone(new_customer)
            self.assertEqual(new_customer.user_id, self.test_uid)
            self.assertTrue(new_customer.is_default)

            found_customer = self.test_dao.get_customer_by_user_id(
                self.test_uid,
            )

            self.assertIsNotNone(found_customer)
            self.assertEqual(found_customer.public_id, new_customer.public_id)

    def test_get_customer_by_public_id(self):
        with app.app_context():
            new_customer = self.test_dao.create_customer(
                'bt_customer_id',
                'cc_token',
                'first_name',
                'last_name',
                self.test_uid,
                is_default=True,
            )

            self.assertIsNotNone(new_customer)
            self.assertEqual(new_customer.user_id, self.test_uid)
            self.assertTrue(new_customer.is_default)

            found_customer = self.test_dao.get_customer_by_public_id(
                new_customer.public_id,
            )

            self.assertIsNotNone(found_customer)
            self.assertEqual(found_customer.public_id, new_customer.public_id)

    def test_get_customer_by_public_id_fail_customer_not_exists(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                self.test_dao.get_customer_by_public_id('INVALID')

                self.assertEqual(e.msg, 'Failed to remove selected customer.')

    def test_create_customer(self):
        with app.app_context():
            new_customer = self.test_dao.create_customer(
                'bt_customer_id',
                'cc_token',
                'first_name',
                'last_name',
                self.test_uid,
                is_default=True,
            )

            self.assertIsNotNone(new_customer)
            self.assertEqual(new_customer.user_id, self.test_uid)
            self.assertTrue(new_customer.is_default)

    def test_create_customer_overwrite_is_default(self):
        with app.app_context():
            self.test_dao.create_customer(
                'bt_customer_id',
                'cc_token',
                'first_name',
                'last_name',
                self.test_uid,
                is_default=True,
            )

            new_customer = self.test_dao.create_customer(
                'bt_customer_id2',
                'cc_token2',
                'first_name2',
                'last_name2',
                self.test_uid,
                is_default=True,
            )

            self.assertIsNotNone(new_customer)
            self.assertEqual(new_customer.user_id, self.test_uid)
            self.assertTrue(new_customer.is_default)

    def test_create_customer_fail_user_not_exists(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                self.test_dao.create_customer(
                    'bt_customer_id',
                    'cc_token',
                    'first_name',
                    'last_name',
                    'INVALID_UUID',
                    is_default=True,
                )

                self.assertEqual(e.msg, 'Failed to create new customer.')

    def test_delete_customer(self):
        with app.app_context():
            new_customer = self.test_dao.create_customer(
                'bt_customer_id',
                'cc_token',
                'first_name',
                'last_name',
                self.test_uid,
                is_default=True,
            )

            self.assertIsNotNone(new_customer)
            self.assertEqual(new_customer.user_id, self.test_uid)
            self.assertTrue(new_customer.is_default)

            deleted_customer = self.test_dao.delete_customer(
                new_customer.public_id
            )

            self.assertIsNotNone(deleted_customer)
            self.assertEqual(
                deleted_customer.public_id,
                new_customer.public_id,
            )

    def test_delete_customer_fail_customer_not_exists(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                self.test_dao.delete_customer('INVALID')
                self.assertEqual(e.msg, 'Failed to remove selected customer.')

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
