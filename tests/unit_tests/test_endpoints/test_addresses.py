import unittest
from http import HTTPStatus

from flask import json

from almanac.utils.security import create_token
from almanac.almanac import app
from almanac.DAOs.user_dao import UserDAO
from almanac.models import db
from almanac.models import (
    UserTable as User,
    AddressTable as Address
)


class EventsEndpointTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

            test_user = User(
                "scheduled_user@email.com",
                "testpw",
                'US/Central',
                'scheduled_user',
            )

            test_delete_user = User(
                "scheduled_delete_user@email.com",
                "testpw",
                'US/Central',
                'deleted_user',
            )

            test_default_user = User(
                "scheduled_default_user@email.com",
                "testpw",
                'US/Central',
                'default_user',
            )

            db.session.add(test_user)
            db.session.add(test_delete_user)
            db.session.add(test_default_user)

            cls.test_user_uid = test_user.public_id
            cls.delete_user_id = test_delete_user.public_id
            cls.default_user_id = test_default_user.public_id
            cls.addresses = []

            for i in range(5):
                new_address = Address(
                    cls.test_user_uid,
                    'first{0}'.format(i),
                    'last{0}'.format(i),
                    'street address1',
                    'Madison',
                    'WI',
                    '53703-{0}'.format(i),
                    'US',
                    is_default=False,
                    extended_address=None
                )

                db.session.add(new_address)
                db.session.commit()
                cls.addresses.append(new_address.public_id)

            delete_address = Address(
                cls.delete_user_id,
                'first-delete',
                'last-delete',
                'street address1',
                'Madison',
                'WI',
                '53703-del',
                'US',
                is_default=True,
                extended_address=None
            )

            db.session.add(delete_address)
            db.session.commit()

            cls.delete_address_id = delete_address.public_id

            default_address = Address(
                cls.default_user_id,
                'first-default',
                'last-default',
                'street address1',
                'Madison',
                'WI',
                '53703-def',
                'US',
                is_default=True,
                extended_address=None
            )

            db.session.add(default_address)
            db.session.commit()

            db.session.add(test_user)
            db.session.commit()

    def test_get_by_public_id(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}/addresses/{1}'.format(
                    self.test_user_uid,
                    self.addresses[0]
                ),
                headers={'jwt': create_token(self.test_user_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(response['first_name'], 'first0')
            self.assertEqual(response['last_name'], 'last0')
            self.assertTrue(response['postal_code'][-1] == '0')

    def test_get_by_public_id_fail_address_not_exists(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}/addresses/{1}'.format(
                    self.test_user_uid,
                    'bad-uuid',
                ),
                headers={
                    'jwt': create_token(self.test_user_uid, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                response['msg'],
                'Failed to find requested address.'
            )

    def test_get_all_addresses(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}/addresses/'.format(
                    self.test_user_uid,
                    'bad-uuid',
                ),
                headers={
                    'jwt': create_token(self.test_user_uid, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(len(response['addresses']), 5)

    def test_get_default_address(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}/addresses/default'.format(
                    self.default_user_id,
                ),
                headers={
                    'jwt': create_token(self.default_user_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(response['is_default'])

    def test_get_default_address_fail_no_default_address(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}/addresses/default'.format(
                    self.test_user_uid,
                ),
                headers={
                    'jwt': create_token(self.test_user_uid, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                response['msg'],
                'Failed to find default address.'
            )

    def test_post(self):
        with app.app_context():
            post_user = User(
                "scheduled_post_user@email.com",
                "testpw",
                'US/Central',
                'scheduled_post_user',
            )
            db.session.add(post_user)
            db.session.commit()

            data = {
                'first_name': 'Bob',
                'last_name': 'Johnson',
                'street_address': '120 E. Washington Ave.',
                'locality': 'Madison',
                'region': 'WI',
                'postal_code': '53703',
                'country_code_alpha2': 'US',
            }

            response = self.test_client.post(
                '/users/{0}/address'.format(
                    post_user.public_id
                ),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(post_user.public_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            for k in data:
                self.assertIsNotNone(response[k])
                self.assertEqual(response[k], data[k])

    def test_post_set_default_overwrites_previous(self):
        with app.app_context():
            post_user = User(
                "default_post_user@email.com",
                "testpw",
                'US/Central',
                'default_post_user',
            )
            db.session.add(post_user)
            db.session.commit()

            new_address = Address(
                post_user.public_id,
                'Bob',
                'Johnson',
                'street address1',
                'Madison',
                'WI',
                '53703',
                'US',
                is_default=True,
                extended_address=None
            )
            db.session.add(new_address)
            db.session.commit()

            data = {
                'first_name': 'Bob',
                'last_name': 'Johnson',
                'street_address': '120 E. Washington Ave.',
                'locality': 'Madison',
                'region': 'WI',
                'postal_code': '53703',
                'country_code_alpha2': 'US',
                'is_default': True,
            }

            response = self.test_client.post(
                '/users/{0}/address'.format(
                    post_user.public_id
                ),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(post_user.public_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            for k in data:
                self.assertIsNotNone(response[k])
                self.assertEqual(response[k], data[k])

            response = self.test_client.get(
                '/users/{0}/addresses/default'.format(
                    post_user.public_id,
                ),
                headers={
                    'jwt': create_token(post_user.public_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            for k in data:
                self.assertIsNotNone(response[k])
                self.assertEqual(response[k], data[k])

    def test_put(self):
        with app.app_context():
            data = {
                'extended_address': 'new extended address.'
            }

            response = self.test_client.put(
                '/users/{0}/addresses/{1}'.format(
                    self.test_user_uid,
                    self.addresses[3],
                ),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_user_uid, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            for k in data:
                self.assertIsNotNone(response[k])
                self.assertEqual(response[k], data[k])

    def test_put_empty_options(self):
        with app.app_context():
            data = {}

            response = self.test_client.put(
                '/users/{0}/addresses/{1}'.format(
                    self.test_user_uid,
                    self.addresses[3],
                ),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(self.test_user_uid, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

    def test_put_set_default_overwrites_previous(self):
        with app.app_context():
            put_user = User(
                "default_put_user@email.com",
                "testpw",
                'US/Central',
                'default_put_user',
            )
            db.session.add(put_user)
            db.session.commit()

            new_address = Address(
                put_user.public_id,
                'Bob',
                'Johnson',
                'street address1',
                'Madison',
                'WI',
                '53703',
                'US',
                is_default=True,
                extended_address=None
            )
            db.session.add(new_address)
            db.session.commit()

            data = {
                'is_default': True,
            }

            response = self.test_client.put(
                '/users/{0}/addresses/{1}'.format(
                    put_user.public_id,
                    new_address.public_id,
                ),
                content_type='application/json',
                data=json.dumps(data),
                headers={
                    'jwt': create_token(put_user.public_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            for k in data:
                self.assertIsNotNone(response[k])
                self.assertEqual(response[k], data[k])

            response = self.test_client.get(
                '/users/{0}/addresses/default'.format(
                    put_user.public_id,
                ),
                headers={
                    'jwt': create_token(put_user.public_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))

            for k in data:
                self.assertIsNotNone(response[k])
                self.assertEqual(response[k], data[k])

    def test_delete(self):
        with app.app_context():
            response = self.test_client.delete(
                '/users/{0}/addresses/{1}'.format(
                    self.delete_user_id,
                    self.delete_address_id,
                ),
                headers={
                    'jwt': create_token(self.delete_user_id, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(response['first_name'], 'first-delete')
            self.assertEqual(response['last_name'], 'last-delete')
            self.assertEqual(response['postal_code'], '53703-del')

    def test_delete_fail_address_not_exists(self):
        with app.app_context():
            response = self.test_client.delete(
                '/users/{0}/addresses/{1}'.format(
                    self.test_user_uid,
                    'bad-uuid'
                ),
                headers={
                    'jwt': create_token(self.test_user_uid, app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                response['msg'],
                'Failed to find requested address.'
            )
