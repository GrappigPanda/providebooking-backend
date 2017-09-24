import unittest

from almanac.almanac import app
from almanac.models import db
from almanac.models import UserTable as User


class UserDAOTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.create_all()
            test_user = User(
                "passwordtest@email.com",
                "testpw",
                'US/Central',
                'passwordtest',
            )

            cls.test_uid = test_user.public_id

            db.session.add(test_user)
            db.session.commit()

    def test_password_correctly_hashes(self):
        with app.app_context():
            found_user = db.session.query(User).filter_by(
                public_id=self.test_uid
            ).first()

            self.assertIsNotNone(found_user)
            self.assertEqual(found_user.email, "passwordtest@email.com")
            self.assertNotEqual(found_user.password, "testpw")
            self.assertTrue(found_user.password.startswith(b'$2b'))

    def test_password_works_after_hash(self):
        with app.app_context():
            found_user = db.session.query(User).filter_by(
                public_id=self.test_uid
            ).first()

            self.assertIsNotNone(found_user)
            self.assertTrue(found_user.compare_password('testpw'))
            self.assertFalse(found_user.compare_password('incorrectpassword'))

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()
