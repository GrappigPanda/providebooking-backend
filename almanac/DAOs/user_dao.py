import logging
import uuid
from http import HTTPStatus

import sqlalchemy
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from almanac.DAOs.base_dao import BaseDAO
from almanac.exc.exceptions import DAOException
from almanac.models import UserTable
from almanac.models import db
from almanac.models import UserTable as User
from almanac.utils.database_utils import exec_and_commit


class UserDAO(BaseDAO):
    """
    Handles user management.
    """

    def get(self, user_id):
        """
        Retrieves a single user by its user id.

        :param str user_id: The User ID to look up.
        :rtype: UserTable
        :return: The UserTable row or None.
        """
        found_user = User.query.filter(
            User.public_id == str(user_id),
            User.is_deleted == False
        ).limit(1).first()

        if found_user is None:
            logging.error(
                'Failed to find requested user by id {0}.'.format(user_id)
            )
            raise DAOException(
                'Failed to find requested user.',
                HTTPStatus.NOT_FOUND,
            )

        return found_user

    def get_by_email(self, email):
        """
        Retrieves user info by the user's email.

        :param str email: The user to retrieve by email. Emails are unique so
        this is a safe retrieval.
        :rtype: UserTable
        :return: The UserTable row or None
        """
        found_user = db.session.query(
            User
        ).filter_by(email=email).first()

        if found_user is None:
            logging.error(
                'Failed to find requested user by email {0}.'.format(email)
            )
            raise DAOException(
                'Failed to find requested user.',
                HTTPStatus.NOT_FOUND,
            )

        return found_user

    def get_by_email_or_username(self, user_challenge):
        """
        Handles retrieving a user by either username or email.

        :param str user_challenge: Email or username.
        :rtype: UserTable
        :return: The found user/email.
        """
        found_user = db.session.query(
            User
        ).filter(
            or_(User.email == user_challenge, User.username == user_challenge)
        ).first()

        if found_user is None:
            logging.error(
                'Failed to find requested user by email/username {0}.'.format(
                    user_challenge,
                )
            )
            raise DAOException(
                'Failed to find requested user.',
                HTTPStatus.NOT_FOUND,
            )

        return found_user

    def get_by_token(self, token, *, is_verify_token=True):
        """
        Retrieves user info by the user's validation token.

        :param str token: The unique validation token for a user.
        :param bool is_verify_token: Toggles if we're fetching by
        `verify_token` or `reset_token`.
        :rtype: UserTable
        :raises: DAOException
        :return: The UserTable row.
        """
        found_user = db.session.query(
            User
        )

        if is_verify_token:
            found_user = found_user.filter_by(
                verify_token=token,
            ).first()
        else:
            found_user = found_user.filter_by(
                reset_token=token,
            ).first()

        if found_user is None:
            logging.error(
                'Failed to find requested account from token {0}.'
            )
            raise DAOException(
                'Failed to find user by validation token.',
                HTTPStatus.NOT_FOUND
            )

        return found_user

    def create_new_user(self, email, password, local_tz, username, *,
                        skip_commit=False):
        """
        Handles the creation of a new user.

        :param str email: The user's email to be registered with the account.
        :param str password: The desired password (not yet hashed).
        :param str local_tz: The local TZ of the user
        :param str username: The desired username for the user.
        :param bool skip_commit: An optional flag used to indicate if we want
        to create the object and add to DB delta, but not commit it just yet.
        Used mostly for facade methods which roll back if the event doesn't
        fully complete (transaction doesn't finalize, &c.).
        :rtype: UserTable
        :return: The newly created user table.
        """
        new_user = User(
            email,
            password,
            local_tz,
            username,
        )

        exec_and_commit(db.session.add, new_user, skip_commit=skip_commit)

        return new_user

    def put(self, user_id, **args):
        _update = {}

        current_user = None
        plaintext = args.get('plaintext_password')
        current_pass = args.get('current_password')
        if plaintext and plaintext != '':
            current_user = self.get(user_id)
            if current_user is None:
                logging.info(
                    'Attempted to update plaintext password for non-existent'
                    'account {0}'.format(user_id)
                )
                raise DAOException(
                    'Requested user to update does not exist.'
                )

        for k, v in args.items():
            if k == 'plaintext_password' and (v != '' or v is not None):
                if UserTable._bcrypt_compare(current_pass, current_user.password):
                    _update['password'] = UserTable._bcrypt_password(plaintext)
                    continue
                else:
                    raise DAOException(
                        'Invalid current password.'
                    )

            if k == 'current_password':
                continue

            _update[k] = v

        if len(_update.keys()) != 0:
            User.query.filter_by(public_id=str(user_id)).update(_update)
            db.session.commit()

        return self.get(user_id)

    def delete(self, user_id):
        """
        Sets a "deleted" flag on the user.

        :param str user_id: The user to "delete".
        :rtype: Boolean
        :return: True if successful execution, exception otherwise.
        """
        User.query.filter_by(
            public_id=str(user_id)
        ).update({
            "is_deleted": True
        })
        db.session.commit()

        return True

    def verify_token(self, token):
        """
        Handles validating an account by its token.

        :param str token: The unique token to validate for.
        :rtype: UserTable
        :return: The validated user.
        """
        found_user = self.get_by_token(token)

        db.session.query(
            User
        ).filter_by(
            public_id=found_user.public_id,
        ).update({
            'is_validated': True,
            'verify_token': None,
        })

        db.session.commit()

        return self.get(found_user.public_id)

    def regenerate_token(self, email, token_choice):
        """
        Handles regenerating a  token for a user.

        :param str email: The user's email to regenerate for.
        :param str token_choice: `verify_token` or `reset_token`.
        :rtype: str
        :returns: The newly generated token.
        """
        found_user = self.get_by_email(email)

        if found_user is None:
            logging.error(
                'Failed to regenerate token for email {0}. '
                'Email not exists.'.format(email)
            )
            raise DAOException(
                'Failed to find requested user account.',
                HTTPStatus.NOT_FOUND
            )

        if found_user.is_validated and token_choice == 'verify_token':
            logging.error('Requested user {0} is already activated. Skipping.')
            raise DAOException('Requested account is already activated.')

        return self._regen_token(email, token_choice), found_user

    def reset_user_password(self, token, plaintext_password):
        """
        Handles resetting a user's password. If failure, throws a DAOException
        with a manual 404.

        :param str token: The user's reset token. Used to verify requesting
        user is who they say they are.
        :param str plaintext_password: The new password.
        :raises: DAOException
        """
        found_user = self.get_by_token(token, is_verify_token=False)

        db.session.query(
            User
        ).filter_by(
            public_id=found_user.public_id
        ).update({
            'password': User._bcrypt_password(plaintext_password),
            'reset_token': None,
        })
        db.session.commit()

        return self.get(found_user.public_id)

    def _regen_token(self, email, token_choice):
        """
        Handles regenerating reset and user verification tokens.

        :param str email: The email to regenerate the password reset token for.
        :param str token_choice: `verify_token` or `reset_token`.
        :rtype: str
        :return: The newly generated token.
        """
        new_token = uuid.uuid4()

        try:
            db.session.query(
                User
            ).filter_by(
                email=email
            ).update({
                token_choice: new_token
            })
            db.session.commit()

            return new_token
        except IntegrityError:
            self._regen_token(email, token_choice)
