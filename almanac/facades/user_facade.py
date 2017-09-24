from sqlite3 import IntegrityError

from flask import current_app

import logging

from almanac.DAOs.address_dao import AddressDAO
from almanac.DAOs.braintree.merchant_dao import MerchantDAO
from almanac.DAOs.mail_queue_dao import MailQueueDAO
from almanac.DAOs.user_dao import UserDAO
from almanac.exc.exceptions import FacadeException, DAOException
from almanac.facades.braintree.submerchant_facade import SubmerchantFacade
from almanac.models import db, SubmerchantTable


class UserFacade(object):
    """
    Handles disparate third-party integrations and user registration in one
    place.
    """

    def get_user_by_email(self, email):
        """
        Retrieves user info by the user's email and other necessary metadata.

        :param str email: The user to retrieve by email. Emails are unique so
        this is a safe retrieval.
        :rtype: UserTable
        :return: The UserTable row or None
        """
        found_user = UserDAO().get_by_email(email)
        return self._add_submerchant_to_user(found_user)

    def get_user_by_id(self, user_id):
        """
        Retrieves a single user by its user id and attaches other necessary
        metadata.

        :param str user_id: The User ID to look up.
        :rtype: UserTable
        :return: The UserTable row or None.
        """
        found_user = UserDAO().get(user_id)
        return self._add_submerchant_to_user(found_user)

    def create_user_as_submerchant(self, email, password, local_tz,
                                   submerchant):
        """
        Handles creating a user and a submerchant at the same time. If either
        fails, nothing is committed to DB and rolled back.

        :param str email: The user's email to be registered with the account.
        :param str password: The desired password (not yet hashed).
        :param str local_tz: The local TZ of the user
        :param dict submerchant: A nested structure which defines all the info
        required to create a submerchant.
        :rtype: UserTable
        :return: The UserTable row or None
        """
        try:
            new_user = UserDAO().create_new_user(
                email,
                password,
                local_tz,
                skip_commit=True
            )

            logging.info(
                'Added new user to database as a submerchant: {0}'.format(
                    new_user,
                )
            )

            new_address = AddressDAO().create_address(
                new_user.public_id,
                submerchant['individual']['first_name'],
                submerchant['individual']['last_name'],
                submerchant['individual']['address']['street_address'],
                submerchant['individual']['address']['locality'],
                submerchant['individual']['address']['region'],
                submerchant['individual']['address']['postal_code'],
                submerchant['individual']['address']['country_code_alpha2'],
                is_default=submerchant['individual']['address']['is_default'],
                skip_commit=True,
            )
            del submerchant['individual']['address']['country_code_alpha2']
            del submerchant['individual']['address']['is_default']

            logging.info(
                'Added new address to database as a submerchant: {0}'.format(
                    new_address,
                )
            )

            new_submerchant = SubmerchantFacade().create_submerchant(
                submerchant,
                new_user.public_id,
                skip_commit=True,
            )

            logging.info(
                'Added new submerchant: {0}'.format(
                    new_submerchant,
                )
            )

            MailQueueDAO().push_to_queue(
                new_user.email,
                'contact@kronikl.io',
                'New Kronikl.io account verification',
                """
                Your new account at Kronikl.io is now available. Please go to
                <a href="http://{0}/verify?q={1}">Verify my account</a>
                to activate your account.
                """.format(
                    'localhost:8080' if current_app.config['ENVIRONMENT'] == 'Dev' else 'app.kronikl.io',
                    new_user.verify_token,
                ),
            )

            db.session.commit()

            return new_user
        except Exception as e:
            db.session.rollback()
            raise e

    def create_user(self, email, password, local_tz, username):
        """
        :param str email: The user's email to be registered with the account.
        :param str password: The desired password (not yet hashed).
        :param str local_tz: The local TZ of the user
        :param str username: The desired username for the new user.
        :rtype: UserTable
        :return: The UserTable row or None
        """
        try:
            new_user = UserDAO().create_new_user(
                email,
                password,
                local_tz,
                username,
                skip_commit=True
            )

            logging.info(
                'Added new user to database as a regular user: {0}'.format(
                    new_user,
                )
            )

            self._send_verification_email(
                new_user.email,
                new_user.verify_token,
            )

            db.session.commit()
            return new_user
        except Exception as e:
            db.session.rollback()
            raise e

    def regenerate_verification_token(self, email):
        """
        Handles regenerating a user's verification token so that they can
        log in.

        :param str email: The user's email.
        """
        token, found_user = UserDAO().regenerate_token(email, 'verify_token')

        logging.info(
            'Regenerated user token for email: {0}'.format(email)
        )

        self._send_verification_email(
            found_user.email,
            token
        )

    def _send_verification_email(self, new_user_email, new_user_token):
        """
        Handles sending a verification email containing the verify token.

        :param new_user_email:
        :param new_user_token:
        :rtype: EmailQueueTable
        :return: The newly created email queue item.
        """
        return MailQueueDAO().push_to_queue(
            new_user_email,
            'contact@kronikl.io',
            'New Kronikl.io account verification',
            """
            Your new account at Kronikl.io is now available. Please go to
            <a href="http://{0}/#/verify/{1}">Verify my account</a>
            to activate your account.
            """.format(
                'localhost:8080' if current_app.config['ENVIRONMENT'] == 'Dev' else 'app.kronikl.io',
                new_user_token,
            ),
        )

    def regenerate_reset_password_token(self, email):
        """
        Regenerates a reset password token and sends another email.

        :param str email: The email of the user who forgot/lost their
        reset password email token.
        :rtype: str
        :return: The newly generated token.
        """
        try:
            new_token, user = UserDAO().regenerate_token(email, 'reset_token')

            MailQueueDAO().push_to_queue(
                'contact@kronikl.io',
                user.email,
                'Please verify your account',
                """
                Your new account at Kronikl.io is now available. Please go to
                <a href="http://{0}/#/reset_password/{1}">Reset my Password</a>
                to activate your account.
                """.format(
                    'localhost:8080'
                    if current_app.config['ENVIRONMENT'] == 'Dev'
                    else 'app.kronikl.io',
                    new_token
                )
            )

            return new_token
        except DAOException as e:
            logging.error(
                'Failed to regenerate reset token with exception: {0}'.format(
                    e
                )
            )

            raise FacadeException(
                'Failed to regenerate reset token.',
                e.status_code
            )

    def _add_submerchant_to_user(self, found_user):
        found_submerchant = MerchantDAO().get_submerchant_by_id(
            found_user.public_id,
        )

        if found_submerchant is not None:
            return found_user + found_submerchant

        return found_user

