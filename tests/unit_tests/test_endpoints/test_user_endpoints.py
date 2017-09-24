import unittest
import json
from http import HTTPStatus

from almanac.almanac import app
from almanac.DAOs.user_dao import UserDAO
from almanac.models import UserTable as User
from almanac.models import db, MasterMerchantTable as MasterMerchant
from almanac.utils.security import create_token


class UserEndpointTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

            test_user = User(
                "test@email.com",
                "testpw",
                'US/Central',
                'test',
            )

            deleted_user = User(
                "delete-test@email.com",
                "testpassword",
                'US/Central',
                'delete-test',
            )
            deleted_user.is_deleted = True

            user_to_delete = User(
                "user-to-delete@email.com",
                "testpw",
                'US/Central',
                'user-to-delete',
            )

            cls.test_uid = test_user.public_id
            cls.deleted_uid = deleted_user.public_id
            cls.to_delete_uid = user_to_delete.public_id

            db.session.add(MasterMerchant('clarksoftware'))
            db.session.add(test_user)
            db.session.add(deleted_user)
            db.session.add(user_to_delete)
            db.session.commit()

    def test_get(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}'.format(self.test_uid),
                headers={'jwt': create_token(self.test_uid, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(response['email'], "test@email.com")

    def test_get_fail_invalid_user_id(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}'.format(self.test_uid + 'alskdjflaksjd'),
                headers={'jwt': create_token(self.test_uid + 'alskdjflaksjd', app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_get_fail_deleted_account(self):
        with app.app_context():
            response = self.test_client.get(
                '/users/{0}'.format(self.deleted_uid),
                headers={'jwt': create_token(self.deleted_uid, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post(self):
        with app.app_context():
            data = {
                'email': 'testpostemail@testpostemail.com',
                'username': 'desiredUsername',
                'plaintext_password': 'testpw',
                'local_tz': 'US/Central'
            }

            response = self.test_client.post(
                '/users/'.format(self.test_uid),
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.test_uid, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(response['email'], data['email'])
            self.assertEqual(response['username'], data['username'])

            found_user = db.session.query(User).filter_by(
                public_id=response['user_id']
            ).first()

            self.assertIsNotNone(found_user)

    def test_post_fail_duplicate_email(self):
        with app.app_context():
            data = {
                'email': 'test@email.com',
                'username': 'testpostfailusername',
                'plaintext_password': 'testpw',
                'local_tz': 'US/Central'
            }

            response = self.test_client.post(
                '/users/'.format(self.test_uid),
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.test_uid, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

    def test_delete(self):
        with app.app_context():
            response = self.test_client.delete(
                '/users/{0}'.format(self.to_delete_uid),
                headers={'jwt': create_token(self.to_delete_uid, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

            deleted_user = db.session.query(User).filter_by(
                public_id=self.to_delete_uid
            ).first()

            self.assertTrue(deleted_user.is_deleted)

    def test_delete_fail_nonexistent_user(self):
        with app.app_context():

            response = self.test_client.delete(
                '/users/{0}'.format('1fe26e77-0c2c-41d3-b6a5-c352a7689131'),
                headers={'jwt': create_token(
                    '1fe26e77-0c2c-41d3-b6a5-c352a7689131',
                    app.config)
                },
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertIsNone(response['email'])

    def test_put_user_preferences(self):
        with app.app_context():
            data = {
                'current_password': 'testpw',
                'plaintext_password': 'testnew-pass',
                'email': 'new_email@test.com',
                'five_min_price': 5.0,
                'fifteen_min_price': 5.0,
                'thirty_min_price': 5.0,
                'sixty_min_price': 5.0,
            }

            response = self.test_client.put(
                '/users/{0}/preferences'.format(self.test_uid),
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.test_uid, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            user_info = db.session.query(User).filter_by(
                public_id=self.test_uid
            ).first()

            self.assertIsNotNone(user_info)

            self.assertEqual(user_info.email, 'new_email@test.com')
            self.assertEqual(user_info.five_min_price, 5.0)
            self.assertEqual(user_info.fifteen_min_price, 5.0)
            self.assertEqual(user_info.thirty_min_price, 5.0)
            self.assertEqual(user_info.sixty_min_price, 5.0)

    def test_put_user_preferences_fail_bad_current_pw(self):
        with app.app_context():
            data = {
                'current_password': 'bad-password',
                'plaintext_password': 'test-pw'
            }

            response = self.test_client.put(
                '/users/{0}/preferences'.format(self.test_uid),
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.test_uid, app.config)},
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                response.get('msg'),
                'Invalid current password.'
            )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class VerificationEndpointsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

            test_user = User(
                "test-verify@email.com",
                "testpw",
                'US/Central',
                'test-verify',
            )

            test_user2 = User(
                "test-verify2@email.com",
                "testpw",
                'US/Central',
                'test-verify2',
            )

            test_user3 = User(
                "test-verify3@email.com",
                "testpw",
                'US/Central',
                'test-verify3',
            )

            cls.test_user_token = test_user.verify_token
            cls.test_uid = test_user.public_id
            cls.test_user2_token = test_user2.verify_token
            cls.test_uid2 = test_user2.public_id
            cls.test_user_email3 = test_user3.email
            cls.test_uid3 = test_user3.public_id

            db.session.add(test_user)
            db.session.add(test_user2)
            db.session.add(test_user3)
            db.session.commit()

    def test_token_verification(self):
        with app.app_context():
            data = {
                'token': self.test_user_token,
            }

            response = self.test_client.post(
                '/users/verify'.format(self.test_uid),
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            found_user = UserDAO().get(self.test_uid)

            self.assertIsNotNone(found_user)
            self.assertIsNone(found_user.verify_token)
            self.assertTrue(found_user.is_validated)

    def test_token_verification_fail_invalid_token(self):
        with app.app_context():
            data = {
                'token': 'asldkfjalksdjf',
            }

            response = self.test_client.post(
                '/users/verify'.format(self.test_uid2),
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

            found_user = UserDAO().get(self.test_uid2)

            self.assertIsNotNone(found_user)
            self.assertIsNotNone(found_user.verify_token)
            self.assertFalse(found_user.is_validated)

    def test_regenerate_token(self):
        with app.app_context():
            found_user = UserDAO().get(self.test_uid3)
            self.assertIsNotNone(found_user)
            original_token = found_user.verify_token

            data = {
                'email': self.test_user_email3,
            }

            response = self.test_client.put(
                '/users/verify'.format(self.test_uid3),
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

            found_user = UserDAO().get(self.test_uid3)

            self.assertIsNotNone(found_user)
            self.assertIsNotNone(found_user.verify_token)
            self.assertNotEqual(found_user.verify_token, original_token)

    def test_regenerate_token_invalid_email(self):
        with app.app_context():
            data = {
                'email': 'INVALID EMAIL',
            }

            response = self.test_client.put(
                '/users/verify'.format(self.test_uid3),
                content_type='application/json',
                data=json.dumps(data),
            )

            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()

