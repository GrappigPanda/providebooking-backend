import unittest
from http import HTTPStatus
from unittest import mock

from flask import json

from almanac.almanac import app
from almanac.DAOs.braintree.merchant_dao import MerchantDAO
from almanac.exc.exceptions import DAOException
from almanac.models import UserTable as User
from almanac.models import (
    db,
    MasterMerchantTable as MasterMerchant,
    CustomerTable as Customer,
    SubscriptionTable as Subscription,
)
from almanac.utils.security import create_token


class SubscriptionEndpointTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()

    def setUp(self):
        with app.app_context():
            test_user1 = User(
                "sub_user1@email.com",
                "testpw",
                'US/Central',
                'sub_user1',
            )

            test_user2 = User(
                "sub_user2@email.com",
                "testpw",
                'US/Central',
                'sub_user2',
            )

            db.session.add(test_user1)
            db.session.add(test_user2)
            db.session.commit()

            test_customer = Customer(
                'test_id',
                'test_cc',
                'first_name',
                'last_name',
                test_user2.public_id,
            )

            db.session.add(test_customer)
            db.session.commit()

            self.test_id_wo_customer = test_user1.public_id
            self.test_id_with_customer = test_user2.public_id

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

    def test_get_with_subscription(self):
        with app.app_context():
            self.test_create_subscription_with_preixisting_user()

            response = self.test_client.get(
                '/braintree/{0}/subscriptions'.format(
                    self.test_id_with_customer,
                ),
                headers={'jwt': create_token(
                    self.test_id_with_customer, app.config
                )},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

    def test_get_without_subscription(self):
        with app.app_context():
            response = self.test_client.get(
                '/braintree/{0}/subscriptions'.format(
                    self.test_id_wo_customer,
                ),
                headers={'jwt': create_token(
                    self.test_id_wo_customer, app.config
                )},
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            self.assertEqual(response['msg'], 'Failed to retrieve subscription info.')

    @mock.patch('braintree.Customer.create')
    @mock.patch('braintree.Subscription.create')
    def test_create_subscription_no_preixisting_user(self, mock_sub, mock_cust):
        mock_sub.return_value = MockSubSuccess()
        mock_cust.return_value = MockSubSuccess()

        with app.app_context():
            data = {
                'nonce': 'test-nonce',
                'first_name': 'test-first',
                'last_name': 'test-last',
            }

            response = self.test_client.post(
                '/braintree/{0}/subscriptions'.format(
                    self.test_id_wo_customer,
                ),
                headers={'jwt': create_token(
                    self.test_id_wo_customer, app.config
                )},
                data=json.dumps(data),
                content_type='application/json',
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

    @mock.patch('braintree.Customer.create')
    @mock.patch('braintree.Subscription.create')
    def test_create_subscription_with_preixisting_user(self, mock_sub, mock_cust):
        mock_sub.return_value = MockSubSuccess()
        mock_cust.return_value = MockSubSuccess()

        with app.app_context():
            response = self.test_client.post(
                '/braintree/{0}/subscriptions'.format(
                    self.test_id_with_customer,
                ),
                headers={'jwt': create_token(
                    self.test_id_with_customer, app.config
                )},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

    @mock.patch('braintree.Subscription.cancel')
    def test_cancel_sub(self, mock_sub):
        mock_sub.return_value = MockSubSuccess()

        with app.app_context():
            self.test_create_subscription_with_preixisting_user()

            response = self.test_client.delete(
                '/braintree/{0}/subscriptions'.format(
                    self.test_id_with_customer,
                ),
                headers={'jwt': create_token(
                    self.test_id_with_customer, app.config
                )},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

    @mock.patch('braintree.Subscription.cancel')
    def test_cancel_sub_user_has_no_sub(self, mock_sub):
        mock_sub.return_value = MockSubSuccess()

        with app.app_context():
            response = self.test_client.delete(
                '/braintree/{0}/subscriptions'.format(
                    self.test_id_with_customer,
                ),
                headers={'jwt': create_token(
                    self.test_id_with_customer, app.config
                )},
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            self.assertEqual(response['msg'], 'Failed to retrieve subscription info.')

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class MockSubSuccess(object):
    @property
    def is_success(self): return True

    @property
    def customer(self): return {}
