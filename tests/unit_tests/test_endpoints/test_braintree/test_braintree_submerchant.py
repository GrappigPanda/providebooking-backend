from http import HTTPStatus

import unittest
import json

from braintree import WebhookNotification
from braintree import WebhookTesting

from almanac.almanac import app
from almanac.DAOs.braintree.merchant_dao import MerchantDAO
from almanac.models import UserTable as User
from almanac.utils.security import create_token
from almanac.models import (
    db,
    MasterMerchantTable as MasterMerchant,
    SubmerchantTable as Submerchant,
)


class SubmerchantEndpointTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = MerchantDAO()

            db.session.add(MasterMerchant('clarksoftware'))
            db.session.commit()

    def setUp(self):
        with app.app_context():
            test_user = User(
                "scheduling_usersubmerch@email.com",
                "testpw",
                'US/Central',
                'scheduling_usersubmerch',
            )

            db.session.add(test_user)
            db.session.commit()

            self.test_id = test_user.public_id
            self.test_email = test_user.email

    def tearDown(self):
        with app.app_context():
            db.session.query(Submerchant).delete()
            db.session.query(User).delete()
            db.session.commit()

    def test_create_submerchant_register_as_business(self):
        with app.app_context():
            data = {
                'user_id': self.test_id,
                'individual': {
                    'first_name': 'Ian',
                    'last_name': 'Clark',
                    'email': 'ilc.ianclark@gmail.com',
                    'phone': '8303437773',
                    'date_of_birth': '06/29/1992',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'business': {
                    'legal_name': '',
                    'dba_name': '',
                    'tax_id': '',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'funding': {
                    'descriptor': 'Wells Fargo',
                    'destination': 'My Company Name',
                    'account_number': '1123581321',
                    'routing_number': '071101307',
                },

                'tos_accepted': True,
                'register_as_business': True
            }

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(self.test_id),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_id, app.config)
                }
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(response['success'])

    def test_create_submerchant_register_as_individual(self):
        with app.app_context():
            data = {
                'user_id': self.test_id,
                'individual': {
                    'first_name': 'Ian',
                    'last_name': 'Clark',
                    'email': 'ilc.ianclark@gmail.com',
                    'phone': '8303437773',
                    'date_of_birth': '06/29/1992',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'funding': {
                    'descriptor': 'Wells Fargo',
                    'destination': 'My Company Name',
                    'account_number': '1123581321',
                    'routing_number': '071101307',
                },

                'tos_accepted': True,
                'register_as_business': False
            }

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(self.test_id),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(response['success'])

    def test_create_submerchant_fail_user_id_not_exists(self):
        with app.app_context():
            data = {
                'user_id': 'nonexistent-user-id',
                'individual': {
                    'first_name': 'Ian',
                    'last_name': 'Clark',
                    'email': 'ilc.ianclark@gmail.com',
                    'phone': '8303437773',
                    'date_of_birth': '06/29/1992',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'funding': {
                    'descriptor': 'Wells Fargo',
                    'destination': 'My Company Name',
                    'account_number': '1123581321',
                    'routing_number': '071101307',
                },

                'tos_accepted': True,
                'register_as_business': False
            }

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(data['user_id']),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(data['user_id'], app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(
                response['msg'],
                'You already have a submerchant account created.'
            )

    def test_create_submerchant_fail_duplicate_submerchant(self):
        with app.app_context():
            data = {
                'user_id': self.test_id,
                'individual': {
                    'first_name': 'Ian',
                    'last_name': 'Clark',
                    'email': 'ilc.ianclark@gmail.com',
                    'phone': '8303437773',
                    'date_of_birth': '06/29/1992',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'funding': {
                    'descriptor': 'Wells Fargo',
                    'destination': 'My Company Name',
                    'account_number': '1123581321',
                    'routing_number': '071101307',
                },

                'tos_accepted': True,
                'register_as_business': False
            }

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(self.test_id),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(response['success'])

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(self.test_id),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(
                response['msg'],
                'You already have a submerchant account created.'
            )

    def test_create_submerchant_fail_as_business_no_business_details(self):
        with app.app_context():
            data = {
                'user_id': self.test_id,
                'individual': {
                    'first_name': 'Ian',
                    'last_name': 'Clark',
                    'email': 'ilc.ianclark@gmail.com',
                    'phone': '8303437773',
                    'date_of_birth': '06/29/1992',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'funding': {
                    'descriptor': 'Wells Fargo',
                    'destination': 'My Company Name',
                    'account_number': '1123581321',
                    'routing_number': '071101307',
                },

                'tos_accepted': True,
                'register_as_business': True
            }

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(self.test_id),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(response['msg'].startswith(
                'Whenever registering as a business')
            )

    def test_webhook_submerchant_approved(self):
        with app.app_context():
            data = {
                'user_id': self.test_id,
                'individual': {
                    'first_name': 'Ian',
                    'last_name': 'Clark',
                    'email': 'ilc.ianclark@gmail.com',
                    'phone': '8303437773',
                    'date_of_birth': '06/29/1992',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'funding': {
                    'descriptor': 'Wells Fargo',
                    'destination': 'My Company Name',
                    'account_number': '1123581321',
                    'routing_number': '071101307',
                },

                'tos_accepted': True,
                'register_as_business': False
            }

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(self.test_id),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            submerchant = db.session.query(
                Submerchant
            ).first()

            notify = WebhookTesting.sample_notification(
                WebhookNotification.Kind.SubMerchantAccountApproved,
                submerchant.braintree_account_id,
            )

            response = self.test_client.post(
                '/braintree/submerchant/webhook',
                content_type='application/x-www-form-urlencoded',
                data=dict(notify),
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

            submerchant = db.session.query(
                Submerchant
            ).filter_by(
                public_id=submerchant.public_id,
            ).first()

            self.assertTrue(submerchant.is_approved)
            self.assertFalse(submerchant.is_rejected)

    def test_webhook_submerchant_rejected(self):
        with app.app_context():
            data = {
                'user_id': self.test_id,
                'individual': {
                    'first_name': 'Ian',
                    'last_name': 'Clark',
                    'email': 'ilc.ianclark@gmail.com',
                    'phone': '8303437773',
                    'date_of_birth': '06/29/1992',
                    'address': {
                        'street_address': '1024 Road',
                        'locality': 'Madison',
                        'region': 'WI',
                        'postal_code': '78028',
                    }
                },
                'funding': {
                    'descriptor': 'Wells Fargo',
                    'destination': 'My Company Name',
                    'account_number': '1123581321',
                    'routing_number': '071101307',
                },

                'tos_accepted': True,
                'register_as_business': False
            }

            response = self.test_client.post(
                '/braintree/{0}/submerchant'.format(self.test_id),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            submerchant = db.session.query(
                Submerchant
            ).first()

            notify = WebhookTesting.sample_notification(
                WebhookNotification.Kind.SubMerchantAccountDeclined,
                submerchant.braintree_account_id,
            )

            response = self.test_client.post(
                '/braintree/submerchant/webhook',
                content_type='application/x-www-form-urlencoded',
                data=dict(notify),
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

            submerchant = db.session.query(
                Submerchant
            ).filter_by(
                public_id=submerchant.public_id,
            ).first()

            self.assertFalse(submerchant.is_approved)
            self.assertTrue(submerchant.is_rejected)

            response = self.test_client.get(
                '/users/{0}'.format(self.test_id),
                headers={'jwt': create_token(self.test_id, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertFalse(response['is_approved'])
            self.assertTrue(response['is_rejected'])
            self.assertTrue(response['has_deposit_account'])

            response = self.test_client.get(
                '/users/email/{0}'.format(self.test_email),
                headers={'jwt': create_token(self.test_id, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertFalse(response['is_approved'])
            self.assertTrue(response['is_rejected'])
            self.assertTrue(response['has_deposit_account'])


    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()

