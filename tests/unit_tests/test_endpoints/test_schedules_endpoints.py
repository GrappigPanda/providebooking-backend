from http import HTTPStatus
from datetime import datetime, timedelta

import unittest
import json

from almanac.almanac import app
from almanac.DAOs.user_dao import UserDAO
from almanac.models import db
from almanac.models import UserTable as User, ScheduleTable as Schedule


class SchedulesEndpointTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            app.config['TESTING'] = True

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

            cls.test_uid = test_user.public_id

            db.session.add(test_user)
            db.session.commit()

            cls.schedule_ids = []
            for i in range(10):
                start_time = datetime.utcnow()
                end_time = datetime.utcnow() + timedelta(minutes=60)
                if i >= 7:
                    start_time = datetime.utcnow() + timedelta(minutes=120)
                    end_time = datetime.utcnow() + timedelta(minutes=180)

                new_schedule = Schedule(
                    start_time,
                    end_time,
                    cls.test_uid,
                    'US/Central'
                )

                db.session.add(new_schedule)
                db.session.commit()
                cls.schedule_ids.append(new_schedule.public_id)

    def test_get(self):
        with app.app_context():
            response = self.test_client.get(
                '/schedules/{0}'.format(self.test_uid)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))['schedules']
            self.assertGreaterEqual(len(response), 10)

    def test_get_schedules(self):
        with app.app_context():
            test_user = User(
                "splitSchedules@email.com",
                "testpw",
                'US/Central',
                'splitSchedules',
            )

            db.session.add(test_user)
            db.session.commit()

            sched1 = Schedule(
                datetime(
                    12,
                    datetime.today().month,
                    datetime.today().day,
                    0,
                    00,
                    00
                ),
                datetime(
                    12,
                    datetime.today().month,
                    datetime.today().day,
                    1,
                    00,
                    0
                ),
                test_user.public_id,
                test_user.local_tz
            )

            sched2 = Schedule(
                datetime(
                    12,
                    datetime.today().month,
                    datetime.today().day,
                    2,
                    00,
                    0
                ),
                datetime(
                    12,
                    datetime.today().month,
                    datetime.today().day + 1,
                    3,
                    00,
                    00
                ),
                test_user.public_id,
                test_user.local_tz
            )

            db.session.add(sched1)
            db.session.add(sched2)
            db.session.commit()

            response = self.test_client.get(
                '/schedules/{0}'.format(test_user.public_id)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            schedules = json.loads(response.data.decode('utf-8'))['schedules']

            self.assertEqual(len(schedules), 2)

    def test_get_by_schedule_id(self):
        with app.app_context():
            response = self.test_client.get(
                '/schedules/{0}/{1}'.format(
                    self.test_uid,
                    self.schedule_ids[2]
                )
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(
                str(response.data.decode('utf-8'))
            )['schedules']

            for k in response.keys():
                self.assertIsNotNone(response[k])

    def test_get_with_time_offset(self):
        with app.app_context():
            data = {
                'time_period_offset': 2
            }

            response = self.test_client.get(
                '/schedules/{0}/{1}'.format(
                    self.test_uid,
                    self.schedule_ids[2]
                ),
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))['schedules']
            self.assertGreaterEqual(len(response), 4)

    def test_get_fail_by_schedule_id(self):
        with app.app_context():
            response = self.test_client.get(
                '/schedules/{0}/123412341234'.format(self.test_uid)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))['schedules']

            for k in response.keys():
                self.assertIsNone(response[k])

    def test_post(self):
        with app.app_context():
            data = {
                'start_time': (
                    datetime.utcnow() + timedelta(minutes=120)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': (
                    datetime.utcnow() + timedelta(minutes=180)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'title': 'Test title'
            }

            response = self.test_client.post(
                '/schedules/{0}'.format(self.test_uid),
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))

            self.assertEqual(response['user_id'], str(self.test_uid))

    def test_put_fail_invalid_schedule_id(self):
        with app.app_context():
            data = {
                'start_time': (
                    datetime.utcnow() + timedelta(minutes=60)
                ).strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': (
                    datetime.utcnow() + timedelta(minutes=120)
                ).strftime('%Y-%m-%d %H:%M:%S')
            }

            response = self.test_client.put(
                '/schedules/{0}/123412341234'.format(self.test_uid),
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                response['msg'],
                'Requested schedule is invalid. Try again.'
            )

    def test_delete(self):
        with app.app_context():
            new_schedule = Schedule(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=60),
                self.test_uid,
                'US/Central'
            )

            db.session.add(new_schedule)
            db.session.commit()

            response = self.test_client.delete(
                '/schedules/{0}/{1}'.format(
                    self.test_uid,
                    new_schedule.public_id
                )
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIsNotNone(response)

    def test_delete_fail_invalid_schedule_id(self):
        with app.app_context():
            response = self.test_client.delete(
                '/schedules/{0}/{1}'.format(
                    self.test_uid,
                    '123412341234'
                )
            )

            self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
            self.assertIsNotNone(response)

            response = json.loads(str(response.data.decode('utf-8')))
            self.assertEqual(
                response['msg'],
                'Failed to delete schedule. Schedule not found.'
            )

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            app.config['TESTING'] = False
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()