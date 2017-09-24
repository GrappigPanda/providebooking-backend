from http import HTTPStatus

import unittest
import json


from almanac.almanac import app
from almanac.DAOs.user_dao import UserDAO
from almanac.models import db
from almanac.models import UserTable as User


class AuthEndpointTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

            test_user = User(
                'auth_test_user@email.com',
                'testpw',
                'US/Central',
                'auth_test_user',
            )

            db.session.add(test_user)
            db.session.commit()

            cls.scheduled_uid = test_user.public_id

    def test_login(self):
        with app.app_context():
            data = {
                'user_challenge': 'auth_test_user@email.com',
                'plaintext_password': 'testpw'
            }

            response = self.test_client.post(
                '/authentication/login'.format(self.scheduled_uid),
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_by_username(self):
        with app.app_context():
            data = {
                'user_challenge': 'auth_test_user',
                'plaintext_password': 'testpw'
            }

            response = self.test_client.post(
                '/authentication/login'.format(self.scheduled_uid),
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_login_fail_invalid_password(self):
        with app.app_context():
            data = {
                'user_challenge': 'auth_test_user@email.com',
                'plaintext_password': 'badpassword'
            }

            response = self.test_client.post(
                '/authentication/login'.format(self.scheduled_uid),
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))

            self.assertEqual(
                response['msg'],
                'Invalid credentials. Try again.'
            )

    def test_login_fail_invalid_email(self):
        with app.app_context():
            data = {
                'user_challenge': 'usernotexists@email.com',
                'plaintext_password': 'testpw'
            }

            response = self.test_client.post(
                '/authentication/login'.format(self.scheduled_uid),
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

