import unittest
import json
from http import HTTPStatus

from almanac.DAOs.user_dao import UserDAO
from almanac.models import db, UserTable as User
from almanac.almanac import create_app

app = create_app(None)


class TestUserRestPasswordTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

            test_user = User(
                'test-verify@email.com',
                'testpw',
                'US/Central',
                'test5',
            )

            cls.test_user_token = test_user.verify_token
            cls.test_uid = test_user.public_id

            db.session.add(test_user)
            db.session.commit()

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

    def test_reset_password(self):
        with app.app_context():
            found_user = UserDAO().get(self.test_uid)
            self.assertIsNotNone(found_user)
            original_token = found_user.reset_token

            data = {
                'email': self.test_user_email,
            }

            response = self.test_client.put(
                '/users/reset_password',
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

            found_user = UserDAO().get(self.test_uid)

            self.assertIsNotNone(found_user)
            self.assertIsNotNone(found_user.reset_token)
            self.assertNotEqual(found_user.reset_token, original_token)

    def test_reset_password_token_resets_password(self):
        with app.app_context():
            found_user = UserDAO().get(self.test_uid)
            self.assertIsNotNone(found_user)
            original_token = found_user.reset_token
            original_password = found_user.password

            data = {
                'email': self.test_user_email,
            }

            response = self.test_client.put(
                '/users/reset_password',
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

            found_user = UserDAO().get(self.test_uid)

            self.assertIsNotNone(found_user)
            self.assertIsNotNone(found_user.reset_token)
            self.assertNotEqual(found_user.reset_token, original_token)

            # Now reset the password and verify it worked..
            data = {
                'token': found_user.reset_token,
                'plaintext_password': 'new_password'
            }

            response = self.test_client.post(
                '/users/reset_password',
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

            found_user = UserDAO().get(self.test_uid)

            self.assertIsNotNone(found_user)
            self.assertIsNone(found_user.reset_token)

            self.assertNotEqual(found_user.password, original_password)
            # Verify new password works.
            self.assertTrue(
                User._bcrypt_compare(
                    data['plaintext_password'],
                    found_user.password
                )
            )

            # Kind of a duplicate, but verify old doesn't work.
            self.assertFalse(
                User._bcrypt_compare(
                    data['plaintext_password'],
                    original_password
                )
            )

    def test_reset_fail_user_not_exists(self):
        with app.app_context():
            data = {
                'email': 'NONEXISTENT@EMAIL.COM',
            }

            response = self.test_client.put(
                '/users/reset_password',
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
