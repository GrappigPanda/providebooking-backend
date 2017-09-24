from almanac.exc.exceptions import DAOException
from almanac.DAOs.base_dao import BaseDAO
from almanac.DAOs.user_dao import UserDAO


class AuthDAO(BaseDAO):
    """
    Handles authentication.
    """

    def login(self, user_challenge, plaintext_password):
        """
        Handles logging in a user.

        :param str user_challenge: The email/username to get the user by
        :param str plaintext_password: The password to compare against.
        :raises: BadPasswordException
        :rtype: UserTable
        :return: The logged in user.
        """
        user_dao = UserDAO()
        user_info = user_dao.get_by_email_or_username(user_challenge)

        if user_info is None:
            raise DAOException("Invalid email. User does not exist.")

        if user_info.compare_password(plaintext_password):
            return user_info

        raise DAOException("Invalid credentials. Try again.")

