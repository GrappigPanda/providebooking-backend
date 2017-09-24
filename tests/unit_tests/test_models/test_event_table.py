from datetime import datetime, timedelta
import unittest

from almanac.almanac import app
from almanac.models import db
from almanac.models import EventTable as Event
from almanac.models import UserTable as User, SubmerchantTable as Submerchant


class UserDAOTestCase(unittest.TestCase):

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

            db.session.commit()

            cls.scheduled_user = User.query.filter_by(
                public_id=cls.scheduled_user.public_id
            ).first().public_id

            cls.scheduling_user = User.query.filter_by(
                public_id=cls.scheduling_user.public_id
            ).first().public_id

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

    def test_calculate_prices(self):
        with app.app_context():
            User.query.filter_by(
                public_id=self.scheduled_user
            ).update({
                'sixty_min_price': 15.0
            })

            new_event = Event(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=60),
                self.scheduling_user,
                self.scheduled_user
            )

            db.session.add(new_event)
            db.session.commit()

            self.assertAlmostEqual(float(15.575), float(new_event.total_price), delta=float(0.2))

    def test_calculate_prices_is_premium(self):
        with app.app_context():
            User.query.filter_by(
                public_id=self.scheduled_user
            ).update({
                'is_premium': True,
                'five_min_price': 2.0
            })

            db.session.commit()

            new_event = Event(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=5),
                self.scheduling_user,
                self.scheduled_user,
            )

            db.session.add(new_event)
            db.session.commit()

            self.assertAlmostEqual(float(new_event.total_price), 2.25, delta=0.2)

    def test_calculate_service_fee(self):
        with app.app_context():
            User.query.filter_by(
                public_id=self.scheduled_user
            ).update({
                'is_premium': True,
                'five_min_price': 100.0
            })

            db.session.commit()

            new_event = Event(
                datetime.utcnow(),
                datetime.utcnow() + timedelta(minutes=5),
                self.scheduling_user,
                self.scheduled_user,
                )

            db.session.add(new_event)
            db.session.commit()

            self.assertAlmostEqual(float(new_event.total_price), 102.7, delta=0.2)
            self.assertAlmostEqual(float(new_event.service_fee), 2.5, delta=0.2)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            if app.config['TEAR_DOWN_AFTER']:
                db.drop_all()
