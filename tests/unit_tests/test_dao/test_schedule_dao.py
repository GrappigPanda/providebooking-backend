import unittest
from datetime import datetime, timedelta

from almanac.almanac import app
from almanac.exc.exceptions import DAOException
from almanac.DAOs.schedule_dao import ScheduleDAO
from almanac.models import db
from almanac.models import UserTable as User
from almanac.models import ScheduleTable as Schedule


class ScheduleDAOGetTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.create_all()

            cls.test_dao = ScheduleDAO()

            test_user = User(
                "schedulefactest@email.com",
                "testpw",
                'US/Central',
                'schedulefactest',
            )

            cls.test_uid = test_user.public_id

            db.session.add(test_user)
            db.session.commit()

    def test_get_all_defaults(self):
        with app.app_context():
            for i in range(10):
                schedule = Schedule(
                    datetime.utcnow() + timedelta(hours=5),
                    datetime.utcnow() + timedelta(hours=6),
                    self.test_uid,
                    'US/Central'
                )

                if i > 7:
                    schedule.end_date = datetime.utcnow() + timedelta(days=32)

                db.session.add(schedule)

            db.session.commit()

            response = self.test_dao.get(self.test_uid)
            self.assertNotEqual([], response)
            self.assertIsNotNone(response)

    def test_get_3_months_ahead(self):
        with app.app_context():
            for i in range(3):
                schedule = Schedule(
                    datetime.utcnow() + timedelta(days=96) + timedelta(hours=i),
                    datetime.utcnow() + timedelta(days=96) + timedelta(hours=i*3),
                    str(self.test_uid),
                    'US/Central'
                )

                db.session.add(schedule)

            db.session.commit()

            response = self.test_dao.get(
                str(self.test_uid),
                time_period_offset=3
            )

            self.assertNotEqual([], response)
            self.assertIsNotNone(response)

    def test_get_3_months_behind(self):
        with app.app_context():
            for i in range(3):
                schedule = Schedule(
                    datetime.utcnow() + timedelta(days=-90, hours=2),
                    datetime.utcnow() + timedelta(days=-90, hours=5),
                    self.test_uid,
                    'US/Central'
                )

                db.session.add(schedule)

            db.session.commit()

            response = self.test_dao.get(
                self.test_uid,
                time_period_offset=-3
            )

            self.assertNotEqual([], response)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class UserDAOPostTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = ScheduleDAO()

            test_user = User(
                "schedulepostfactest@email.com",
                "testpw",
                'US/Central',
                'schedulepostfactest',
            )

            cls.test_uid = test_user.public_id

            db.session.add(test_user)
            db.session.commit()

    def test_post(self):
        with app.app_context():
            start = datetime.utcnow().replace(hour=2) + timedelta(days=1)
            end = datetime.utcnow().replace(hour=5) + timedelta(days=1)

            schedule = self.test_dao.post(
                start,
                end,
                self.test_uid,
            )

            self.assertIsNotNone(schedule)
            self.assertEqual(start.hour, schedule.utc_open.hour)
            self.assertEqual(start.minute, schedule.utc_open.minute)
            self.assertEqual(end.hour, schedule.utc_end.hour)
            self.assertEqual(end.minute, schedule.utc_end.minute)

    def test_post_fail_entry_exists(self):
        with app.app_context():
            start = datetime.utcnow()
            end = datetime.utcnow() + timedelta(minutes=5)

            db.session.add(Schedule(
                start,
                end,
                self.test_uid,
                'US/Central'
            ))
            db.session.commit()

            try:
                self.test_dao.post(
                    datetime.utcnow() + timedelta(minutes=2),
                    datetime.utcnow() + timedelta(minutes=3),
                    self.test_uid
                )
            except DAOException as e:
                self.assertEqual(
                    e.msg,
                    "Invalid schedule. This overlaps with a previous schedule."
                )

    def test_post_fail_negative_duration(self):
        with app.app_context():
            try:
                self.test_dao.post(
                    datetime.utcnow() + timedelta(days=1),
                    datetime.utcnow(),
                    self.test_uid
                )
            except DAOException as e:
                self.assertEqual(
                    e.msg,
                    "Invalid start time. Start must be before the end."
                )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class UserDAODeleteTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = ScheduleDAO()

            test_user = User(
                "scheduledeletefactest@email.com",
                "testpw",
                'US/Central',
                'scheduledeletefactest',
            )

            test2_user = User(
                "scheduledeletedontuse@email",
                "testpw",
                'US/Central',
                'scheduledeletefactest2',
            )

            cls.test_uid = test_user.public_id
            cls.other_uid = test2_user.public_id

            db.session.add(test_user)
            db.session.add(test2_user)
            db.session.commit()

    def test_delete(self):
        with app.app_context():
            new_schedule = Schedule(
                datetime.utcnow() + timedelta(hours=2),
                datetime.utcnow() + timedelta(hours=5),
                self.test_uid,
                'US/Central'
            )
            db.session.add(new_schedule)
            db.session.commit()

            self.test_dao.delete(
                self.test_uid,
                new_schedule.public_id
            )

    def test_delete_fail_not_users_schedule(self):
        with app.app_context():
            with self.assertRaises(DAOException):
                new_schedule = Schedule(
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(minutes=5),
                    self.other_uid,
                    'US/Central'
                )
                db.session.add(new_schedule)
                db.session.commit()

                self.test_dao.delete(
                    self.test_uid,
                    new_schedule.public_id
                )

    def test_delete_fail_schedule_not_exist(self):
        with app.app_context():
            with self.assertRaises(DAOException):
                self.test_dao.delete(
                    self.test_uid,
                    "10000000"
                )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class UserDAOPutTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = ScheduleDAO()

            test_user = User(
                "scheduleputfactest@email.com",
                "testpw",
                'US/Central',
                'scheduleputfactest',
            )

            test2_user = User(
                "scheduleputotheruser@email.com",
                "testpw",
                'US/Central',
                'scheduleputotheruser',
            )

            cls.test_uid = test_user.public_id
            cls.other_uid = test2_user.public_id

            db.session.add(test_user)
            db.session.add(test2_user)
            db.session.commit()

    def test_put(self):
        with app.app_context():
            new_schedule = Schedule(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=5),
                self.test_uid,
                'US/Central'
            )

            new_schedule.public_id = 'ed311073-076e-485e-a226-801c2254a173'
            db.session.add(new_schedule)
            db.session.commit()

            start = datetime.utcnow() + timedelta(minutes=2)
            end = datetime.utcnow() + timedelta(minutes=7)
            response = self.test_dao.put(
                new_schedule.public_id,
                start,
                end,
                self.test_uid
            )

            self.assertIsNotNone(response)
            self.assertEqual(start.hour, response.utc_open.hour)
            self.assertEqual(start.minute, response.utc_open.minute)
            self.assertEqual(end.hour, response.utc_end.hour)
            self.assertEqual(end.minute, response.utc_end.minute)

    def test_put_fail_schedule_not_exists(self):
        with app.app_context():
            with self.assertRaises(DAOException):
                start = datetime.utcnow() + timedelta(minutes=2)
                end = datetime.utcnow() + timedelta(minutes=7)
                response = self.test_dao.put(
                    "10000000",
                    start,
                    end,
                    self.test_uid
                )

                self.assertIsNone(response)

    def test_put_fail_invalid_duration(self):
        with app.app_context():
            new_schedule = Schedule(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=5),
                self.test_uid,
                'US/Central'
            )
            db.session.add(new_schedule)
            db.session.commit()

            try:
                start = datetime.utcnow() + timedelta(minutes=2)
                end = datetime.utcnow() + timedelta(minutes=7)
                self.test_dao.put(
                    new_schedule.public_id,
                    start,
                    end,
                    self.test_uid
                )
            except DAOException as e:
                self.assertEqual(
                    e.msg,
                    "Invalid start time. Start must be before the end."
                )

    def test_put_fail_other_users_schedule(self):
        with app.app_context():
            with self.assertRaises(DAOException):
                new_schedule = Schedule(
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(minutes=5),
                    self.other_uid,
                    'US/Central'
                )
                db.session.add(new_schedule)
                db.session.commit()

                start = datetime.utcnow() + timedelta(minutes=2)
                end = datetime.utcnow() + timedelta(minutes=7)
                response = self.test_dao.put(
                    new_schedule.public_id,
                    start,
                    end,
                    self.test_uid
                )

                self.assertIsNone(response)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()

