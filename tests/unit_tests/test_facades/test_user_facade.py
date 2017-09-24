import unittest
from unittest import mock

from almanac.almanac import app
from almanac.exc.exceptions import SQLException
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

            cls.test_facade = UserFacade()

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
                'test2',
            )
            deleted_user.is_deleted = True

            user_to_delete = User(
                "user-to-delete@email.com",
                "testpw",
                'US/Central',
                'test3'
            )

            cls.test_uid = test_user.public_id
            cls.deleted_uid = deleted_user.public_id
            cls.to_delete_uid = user_to_delete.public_id

            db.session.add(test_user)
            db.session.add(deleted_user)
            db.session.add(user_to_delete)
            db.session.commit()

    def test_create_user_adds_to_mail_queue(self):
        with app.app_context():
            new_user = self.test_facade.create_user(
                "test1-email-queue@email.com",
                "testpw",
                'US/Central',
                'test4',
            )

            found_user = db.session.query(User).filter_by(
                email=new_user.email
            ).first()

            self.assertIsNotNone(found_user)

            found_mail_queue = db.session.query(
                EmailQueue
            ).filter_by(
                email_to=new_user.email
            ).first()

            self.assertIsNotNone(found_mail_queue)
            self.assertTrue(
                found_user.verify_token in found_mail_queue.body
            )

    @mock.patch('almanac.DAOs.mail_queue_dao.MailQueueDAO.push_to_queue')
    def test_create_user_mail_queue_failure(self, mail_queue):
        mail_queue.side_effect = SQLException('Test')

        with app.app_context():
            try:
                new_user = self.test_facade.create_user(
                    "test2-email-queue@email.com",
                    "testpw",
                    'US/Central',
                    'test12341234',
                )
            except Exception as e:
                pass

            found_user = db.session.query(User).filter_by(
                email='test2-email-queue@email.com'
            ).first()

            self.assertIsNone(found_user)

            found_mail_queue = db.session.query(
                EmailQueue
            ).filter_by(
                email_to='test2-email-queue@email.com'
            ).first()

            self.assertIsNone(found_mail_queue)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()
