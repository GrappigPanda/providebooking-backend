from datetime import datetime, timedelta
from unittest import mock

import unittest

from almanac.almanac import app
from almanac.exc.exceptions import DAOException, FacadeException
from almanac.facades.paid_event_facade import EventFacade
from almanac.models import db
from almanac.models import UserTable as User, AddressTable as Address
from almanac.models import ScheduleTable as Schedule
from almanac.models import EventTable as Event, SubmerchantTable as Submerchant


class TestPaidEventFacade(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with app.app_context():
            db.drop_all()
            db.create_all()

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
                    datetime.utcnow().replace(hour=3) + timedelta(days=1),
                    datetime.utcnow().replace(hour=8) + timedelta(days=1),
                    self.scheduled_user,
                    'UTC',
                )

                db.session.add(new_schedule)
                db.session.commit()

                transaction_mock.side_effect = DAOException('test')

                EventFacade().create_new_event(
                    self.scheduling_user,
                    self.scheduled_user,
                    (datetime.utcnow().replace(hour=4) + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    (datetime.utcnow().replace(hour=5) + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
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

