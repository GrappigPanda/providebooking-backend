import random
from datetime import datetime, timedelta

import unittest
from unittest import mock

import pytz

from almanac.almanac import app
from almanac.exc.exceptions import DAOException, FacadeException
from almanac.DAOs.event_dao import EventDAO
from almanac.facades.paid_event_facade import EventFacade
from almanac.models import db
from almanac.models import UserTable as User, AddressTable as Address
from almanac.models import ScheduleTable as Schedule
from almanac.models import EventTable as Event, SubmerchantTable as Submerchant


class EventDAOGetTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = EventDAO()

            cls.scheduling_user = User(
                "scheduling_user@email.com",
                "testpw",
                'US/Central',
                'scheduling_user',
            )

            cls.scheduled_user = User(
                "scheduled_user@email.com",
                "testpw",
                'US/Central',
                'scheduled_user',
            )

            db.session.add(cls.scheduling_user)
            db.session.add(cls.scheduled_user)

            db.session.commit()

            cls.scheduled_user = User.query.filter_by(
                public_id=cls.scheduled_user.public_id
            ).first().public_id

            cls.scheduling_user = User.query.filter_by(
                public_id=cls.scheduling_user.public_id
            ).first().public_id

            User.query.filter_by(
                public_id=cls.scheduled_user
            ).update({
                'sixty_min_price': 15
            })

            db.session.add(Submerchant(
                cls.scheduled_user,
                'testaccountid',
                'firstName',
                'LastName',
                'email',
                datetime.utcnow() + timedelta(days=-365*20),
                'address_street',
                'address_locality',
                'address_region',
                'address_zip',
                ))

            db.session.commit()

            cls.eids = []
            for i in range(3):
                new_event = Event(
                    datetime.utcnow(),
                    datetime.utcnow() + timedelta(minutes=60),
                    cls.scheduling_user,
                    cls.scheduled_user,
                )

                db.session.add(new_event)

                db.session.commit()

                cls.eids.append(new_event.public_id)

    def test_get_for_scheduling_user(self):
        with app.app_context():
            response = self.test_dao.get_for_scheduling_user(
                self.scheduling_user
            )

            self.assertNotEqual([], response)
            self.assertEqual(len(response), 3)

    def test_get_for_scheduled_user(self):
        with app.app_context():
            response = self.test_dao.get_for_scheduled_user(
                self.scheduled_user
            )

            self.assertNotEqual([], response)
            self.assertEqual(len(response), 3)

    def test_get_by_event_id(self):
        with app.app_context():
            response = self.test_dao.get_by_event_id(
                self.scheduled_user,
                self.eids[1]
            )

            self.assertIsNotNone(response)
            self.assertEqual(response.EventTable.public_id, self.eids[1])

    def test_get_by_event_fail_no_eid(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                self.test_dao.get_by_event_id(
                    self.scheduled_user,
                    '1000000',
                )

                self.assertTrue(
                    e.msg.startswith(
                        'Failed to retrieve event ('
                    )
                )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class EventDAOPostTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = EventDAO()

            cls.scheduling_user = User(
                "scheduling_user@email.com",
                "testpw",
                'US/Central',
                'scheduling_user',
            )

            cls.scheduled_user = User(
                "scheduled_user@email.com",
                "testpw",
                'US/Central',
                'scheduled_user',
            )

            db.session.add(cls.scheduling_user)
            db.session.add(cls.scheduled_user)

            db.session.commit()

            cls.scheduled_user = User.query.filter_by(
                public_id=cls.scheduled_user.public_id
            ).first().public_id

            cls.scheduling_user = User.query.filter_by(
                public_id=cls.scheduling_user.public_id
            ).first().public_id

            User.query.filter_by(
                public_id=cls.scheduled_user
            ).update({
                'sixty_min_price': 15
            })

            db.session.add(Submerchant(
                cls.scheduled_user,
                'testaccountid',
                'firstName',
                'LastName',
                'email',
                datetime.utcnow() + timedelta(days=-365*20),
                'address_street',
                'address_locality',
                'address_region',
                'address_zip',
                ))

            db.session.commit()

            new_schedule = Schedule(
                datetime.utcnow().replace(hour=0) + timedelta(days=1),
                datetime.utcnow().replace(hour=12) + timedelta(days=1),
                cls.scheduled_user,
                'US/Central'
            )

            db.session.add(new_schedule)
            db.session.commit()

    def test_post(self):
        with app.app_context():
            start_time = datetime.utcnow().replace(hour=1) + timedelta(days=1)
            end_time = datetime.utcnow().replace(hour=5) + timedelta(days=1)

            response = self.test_dao.create_new_event(
                str(self.scheduling_user),
                str(self.scheduled_user),
                start_time.strftime('%Y-%m-%d %H:%M:%S'),
                end_time.strftime('%Y-%m-%d %H:%M:%S'),
                local_tz='US/Central'
            )

            self.assertIsNotNone(response)
            self.assertEqual(
                str(response.scheduling_user_id),
                str(self.scheduling_user)
            )
            self.assertEqual(
                str(response.scheduled_user_id),
                str(self.scheduled_user)
            )

    def test_post_fail_overlapping_events(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:

                start_time = datetime.utcnow() + timedelta(minutes=0)
                end_time = datetime.utcnow() + timedelta(minutes=60)

                self.test_dao.create_new_event(
                    str(self.scheduling_user),
                    str(self.scheduled_user),
                    start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    local_tz='UTC'
                )
                self.assertEqual(
                    e.msg,
                    'Invalid event to be scheduled. '
                    'A pre-existing event exists.'
                )

    def test_post_fail_invalid_duration(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                start_time = datetime.utcnow() + timedelta(minutes=120)
                end_time = datetime.utcnow() + timedelta(minutes=167)

                self.test_dao.create_new_event(
                    str(self.scheduling_user),
                    str(self.scheduled_user),

                    start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    local_tz='US/Central'
                )

                self.assertEqual(
                    e.msg,
                    'Invalid duration. Attempted duration is not of valid '
                    'length.'
                )

    def test_post_fail_negative_duration(self):
        with app.app_context():
            start_time = datetime.utcnow() + timedelta(minutes=240)
            end_time = datetime.utcnow() + timedelta(minutes=180)

            try:
                self.test_dao._assert_valid_duration(start_time, end_time)
            except DAOException as e:
                self.assertEqual(
                    e.msg,
                    'Invalid start time. Start must be before the end.'
                )
                return

            self.assertIsNotNone(None)

    def test_post_scheduled_user_has_no_schedule(self):
        with app.app_context():
            with self.assertRaises(DAOException) as e:
                start_time = datetime.utcnow() + timedelta(hours=-7)
                end_time = datetime.utcnow() + timedelta(hours=-6)

                self.test_dao.create_new_event(
                    self.scheduling_user,
                    self.scheduled_user,
                    start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    local_tz='US/Central'
                )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class TestPaidEventFacade(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_dao = EventDAO()

            cls.scheduling_user = User(
                "scheduling_user@email.com",
                "testpw",
                'US/Central',
                'scheduling_user',
            )

            cls.scheduled_user = User(
                "scheduled_user@email.com",
                "testpw",
                'US/Central',
                'scheduled_user',
            )

            db.session.add(cls.scheduling_user)
            db.session.add(cls.scheduled_user)

            new_default_address = Address(
                cls.scheduling_user.public_id,
                'test-first',
                'test-last',
                'test-street-address',
                'test-locality',
                'test-region',
                '53703',
                'US',
                is_default=True,
            )

            db.session.add(new_default_address)
            db.session.commit()

            db.session.add(Submerchant(
                cls.scheduled_user.public_id,
                'testaccountid',
                'firstName',
                'LastName',
                'email',
                datetime.utcnow() + timedelta(days=-365*20),
                'address_street',
                'address_locality',
                'address_region',
                'address_zip',
                ))


            new_schedule = Schedule(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=3*60),
                cls.scheduled_user.public_id,
                'US/Central'
            )

            db.session.add(new_schedule)
            db.session.commit()

            cls.scheduled_user = User.query.filter_by(
                public_id=cls.scheduled_user.public_id
            ).first().public_id

            cls.scheduling_user = User.query.filter_by(
                public_id=cls.scheduling_user.public_id
            ).first().public_id

            User.query.filter_by(
                public_id=cls.scheduled_user
            ).update({
                'sixty_min_price': 15
            })

            db.session.commit()

    @mock.patch('braintree.Transaction.sale')
    def test_rollback_on_failure(self, transaction_mock):
        with app.app_context():
            with self.assertRaises(FacadeException) as e:
                new_schedule = Schedule(
                    datetime.utcnow().replace(hour=1) + timedelta(days=1),
                    datetime.utcnow().replace(hour=5) + timedelta(days=1),
                    self.scheduled_user,
                    'UTC',
                )

                db.session.add(new_schedule)
                db.session.commit()

                transaction_mock.side_effect = DAOException('test')

                new_event = EventFacade().create_new_event(
                    self.scheduling_user,
                    self.scheduled_user,
                    (datetime.utcnow().replace(hour=2) + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    (datetime.utcnow().replace(hour=3) + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    'UTC',
                    'test3-1234ko1234',
                    'fake-nonce',
                )

                self.assertEqual(e.msg, 'test')

                found_event = db.session.query(
                    Event
                ).filter_by(
                    notes='test3-1234ko1234',
                ).first()

                self.assertIsNone(found_event)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


