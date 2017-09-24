from http import HTTPStatus
from datetime import datetime, timedelta

import unittest
import json
from unittest import mock

from almanac.almanac import app
from almanac.DAOs.user_dao import UserDAO
from almanac.models import db
from almanac.models import (
    UserTable as User,
    ScheduleTable as Schedule,
    SubmerchantTable as Submerchant,
    AddressTable as Address,
    EventTable as Event,
)
from almanac.utils.security import create_token


class EventsEndpointTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

            scheduling = User(
                "scheduling_user@email.com",
                "testpw",
                'US/Central',
                'scheduling_user',
            )

            scheduled = User(
                "scheduled_user@email.com",
                "testpw",
                'US/Central',
                'scheduled_user',
            )

            cls.scheduling_uid = scheduling.public_id
            cls.scheduled_uid = scheduled.public_id

            db.session.add(scheduling)
            db.session.add(scheduled)
            db.session.commit()

            User.query.filter_by(
                public_id=cls.scheduled_uid
            ).update({
                'sixty_min_price': 15
            })

            db.session.add(Submerchant(
                cls.scheduled_uid,
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
                datetime.utcnow() + timedelta(minutes=60),
                cls.scheduled_uid,
                'US/Central'
            )

            db.session.add(new_schedule)
            db.session.commit()

            cls.new_schedule_id = new_schedule.id

    def test_get(self):
        with app.app_context():
            data = {
                'is_scheduling': False
            }

            response = self.test_client.get(
                '/events/{0}'.format(self.scheduled_uid),
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.scheduled_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))['events']

            for event in response:
                for k in event.keys():
                    self.assertIsNone(response[k])

    def test_get_is_scheduling(self):
        with app.app_context():
            data = {
                'is_scheduling': True
            }

            response = self.test_client.get(
                '/events/{0}'.format(self.scheduling_uid),
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.scheduling_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))['events']

            for event in response:
                for k in event.keys():
                    self.assertIsNotNone(event[k])

    def test_get_event_by_id(self):
        with app.app_context():
            new_event = Event(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=60),
                self.scheduling_uid,
                self.scheduled_uid,
                'Test notes'
            )
            new_event.total_price = 5.00
            db.session.add(new_event)
            db.session.commit()

            response = self.test_client.get(
                '/event/{0}/{1}'.format(
                    self.scheduling_uid,
                    str(new_event.public_id)
                ),
                headers={'jwt': create_token(self.scheduling_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                new_event.public_id,
                response['event']['public_id'],
            )

            self.assertEqual(
                new_event.scheduled_user_id,
                response['scheduled_user']['public_id'],
            )

            self.assertEqual(
                new_event.scheduling_user_id,
                response['scheduling_user']['public_id'],
            )

    def test_get_events_with_offset(self):
        with app.app_context():
            new_event = Event(
                datetime.utcnow() + timedelta(days=-90, minutes=-60),
                datetime.utcnow() + timedelta(days=-90, minutes=0),
                self.scheduling_uid,
                self.scheduled_uid
            )
            new_event.total_price = 5.00
            db.session.add(new_event)
            db.session.commit()

            response = self.test_client.get(
                '/event/{0}/{1}?time_period_offset=3'.format(
                    self.scheduling_uid,
                    str(new_event.public_id)
                ),
                headers={'jwt': create_token(self.scheduling_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                new_event.public_id,
                response['event']['public_id']
            )

    def test_get_fail_event_by_id(self):
        with app.app_context():
            response = self.test_client.get(
                '/event/{0}/1000000'.format(self.scheduling_uid),
                headers={'jwt': create_token(self.scheduling_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))

            self.assertEqual(
                'Requested event not found. Please refresh and try again.',
                response['msg'],
            )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()


class PaymentEventEndpointsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

            scheduling = User(
                "scheduling_user1@email.com",
                "testpw",
                'UTC',
                'scheduling_user1',
            )

            scheduled = User(
                "scheduled_user2@email.com",
                "testpw",
                'UTC',
                'scheduled_user2',
            )

            cls.scheduling_uid = scheduling.public_id
            cls.scheduled_uid = scheduled.public_id

            db.session.add(scheduling)
            db.session.add(scheduled)
            db.session.commit()

            default_address = Address(
                cls.scheduling_uid,
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

            User.query.filter_by(
                public_id=cls.scheduled_uid
            ).update({
                'sixty_min_price': 15
            })

            db.session.commit()

            db.session.add(Submerchant(
                cls.scheduled_uid,
                '3bX9oSVaocidZMxWGGMybj',
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
                datetime.utcnow() + timedelta(minutes=60),
                cls.scheduled_uid,
                'UTC'
            )

            db.session.add(new_schedule)
            db.session.commit()

            cls.new_schedule_id = new_schedule.id

    @mock.patch('braintree.Transaction.sale')
    def test_post(self, transaction_mock):
        transaction_mock = True

        with app.app_context():
            new_schedule = Schedule(
                datetime.utcnow().replace(hour=2) + timedelta(days=1),
                datetime.utcnow().replace(hour=7) + timedelta(days=1),
                self.scheduled_uid,
                'UTC',
            )

            db.session.add(new_schedule)
            db.session.commit()

            data = {
                'scheduled_user_id': self.scheduled_uid,
                'localized_start_time': (
                    datetime.utcnow().replace(hour=4) + timedelta(days=1)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'localized_end_time': (
                    datetime.utcnow().replace(hour=5) + timedelta(days=1)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'local_tz': 'UTC',
                'notes': 'Contact me at ian@ianleeclark.com for more info.',
                'is_paid': True,
                'nonce': 'fake-valid-debit-nonce',
            }

            response = self.test_client.post(
                '/events/',
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.scheduling_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(response['notes'], data['notes'])

    @mock.patch('braintree.Transaction.sale')
    def test_post_multiple_hours(self, transaction_mock):
        transaction_mock = True
        with app.app_context():
            new_schedule = Schedule(
                datetime.utcnow().replace(hour=1) + timedelta(days=1),
                datetime.utcnow().replace(hour=5) + timedelta(days=1),
                self.scheduled_uid,
                'UTC',
            )

            db.session.add(new_schedule)
            db.session.commit()

            data = {
                'scheduled_user_id': self.scheduled_uid,
                'localized_start_time': (
                    datetime.utcnow().replace(hour=2) + timedelta(days=1)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'localized_end_time': (
                    datetime.utcnow().replace(hour=4) + timedelta(days=1)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'local_tz': 'US/Central',
                'notes': 'Contact me at ian@ianleeclark.com for more info.',
                'is_paid': True,
                'nonce': 'fake-valid-debit-nonce',
            }

            response = self.test_client.post(
                '/events/',
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.scheduling_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(response['notes'], data['notes'])

    @mock.patch('braintree.Transaction.sale')
    def test_post_fail_gt_60_not_mod(self, transaction_mock):
        transaction_mock = True
        with app.app_context():
            new_schedule = Schedule(
                datetime.utcnow().replace(hour=1) + timedelta(days=1),
                datetime.utcnow().replace(hour=18) + timedelta(days=1),
                self.scheduled_uid,
                'UTC',
            )

            db.session.add(new_schedule)
            db.session.commit()

            data = {
                'scheduled_user_id': self.scheduled_uid,
                'localized_start_time': (
                    datetime.utcnow().replace(hour=2) + timedelta(days=1)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'localized_end_time': (
                    datetime.utcnow().replace(hour=4, minute=37) + timedelta(days=1)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'local_tz': 'US/Central',
                'notes': 'Contact me at ian@ianleeclark.com for info.',
                'is_paid': True,
                'nonce': 'fake-valid-debit-nonce',
            }

            response = self.test_client.post(
                '/events/',
                content_type='application/json',
                data=json.dumps(data),
                headers={'jwt': create_token(self.scheduling_uid, app.config)}
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)
            response = json.loads(str(response.data.decode('utf-8')))
            self.assertTrue(
                response['msg'].startswith("Invalid duration.")
            )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()

