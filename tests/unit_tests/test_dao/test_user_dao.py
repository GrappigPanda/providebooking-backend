import unittest

from almanac.almanac import app
from almanac.exc.exceptions import SQLException, DAOException
from almanac.DAOs.user_dao import UserDAO
from almanac.facades.user_facade import UserFacade
from almanac.models import db
from almanac.models import UserTable as User
from almanac.models import EmailQueueTable as EmailQueue


class UserDAOTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = UserDAO()

            test_user = User(
                "test@email.com",
                "testpw",
                'US/Central',
                'test1',
            )

            deleted_user = User(
                "delete-test@email.com",
                "testpassword",
                'US/Central',
                'test3',
            )
            deleted_user.is_deleted = True

            user_to_delete = User(
                "user-to-delete@email.com",
                "testpw",
                'US/Central',
                'test4',
            )

            cls.test_uid = test_user.public_id
            cls.deleted_uid = deleted_user.public_id
            cls.to_delete_uid = user_to_delete.public_id

            db.session.add(test_user)
            db.session.add(deleted_user)
            db.session.add(user_to_delete)
            db.session.commit()

    def test_get_pass(self):
        with app.app_context():
            response = self.test_dao.get(self.test_uid)
            self.assertIsNotNone(response)
            self.assertEqual(response.email, "test@email.com")

    def test_get_fail_invalid_user_id(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                self.test_dao.get("9981ffba-2126-4afc-ad0b-49cfc29f98d9")

    def test_get_fail_deleted_account(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                self.test_dao.get(self.deleted_uid)

    def test_post(self):
        with app.app_context():
            new_user = self.test_dao.create_new_user(
                "test1@email.com",
                "testpw",
                'US/Central',
                'test10',
            )

            self.assertIsNotNone(new_user)
            self.assertEqual(new_user.email, "test1@email.com")

    def test_post_fail_duplicate_email(self):
        with self.assertRaises(SQLException):
            with app.app_context():
                self.test_dao.create_new_user(
                    "test1@email.com",
                    "testpw",
                    'US/Central',
                    'testalskdjf',
                )

    def test_delete(self):
        with app.app_context():
            response = self.test_dao.delete(self.to_delete_uid)

            self.assertTrue(response)

            deleted_user = db.session.query(User).filter_by(
                public_id=self.to_delete_uid
            ).first()

            self.assertTrue(deleted_user.is_deleted)

    def test_delete_fail_nonexistent_user(self):
        with app.app_context():
            response = self.test_dao.delete(
                "9981ffba-2126-4afc-ad0b-49cfc29f98d9"
            )

            self.assertTrue(response)

    def test_put_empty_doesnt_fail(self):
        with app.app_context():
             self.test_dao.put(self.test_uid, **{})


    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()
