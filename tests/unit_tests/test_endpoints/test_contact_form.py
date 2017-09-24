from http import HTTPStatus
from datetime import datetime, timedelta

import unittest
import json


from almanac.almanac import app
from almanac.DAOs.user_dao import UserDAO
from almanac.models import db
from almanac.models import UserTable as User, ScheduleTable as Schedule
from almanac.models import EventTable as Event


class EventsEndpointTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            app.config['TESTING'] = True

            db.drop_all()
            db.create_all()

            cls.test_client = app.test_client()
            cls.test_dao = UserDAO()

    def test_post(self):
        with app.app_context():
            data = {
                'name': 'Ian Clark',
                'email': 'ian@ianleeclark.com',
                'message': 'Hi your website sucks major fuckign dick, dude kys'
            }

            response = self.test_client.post(
                '/contact',
                content_type='application/json',
                data=json.dumps(data)
            )

            self.assertEqual(response.status_code, HTTPStatus.OK)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            app.config['TESTING'] = False
