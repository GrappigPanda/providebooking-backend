from almanac.DAOs.base_dao import BaseDAO
from almanac.models import db
from almanac.models.contact_table import ContactTable as Contact
from almanac.utils.database_utils import exec_and_commit


class ContactUsDAO(BaseDAO):
    """
    Handles "contact us" form.
    """

    def add_new_contact_message(self, name, message, email):
        """
        Handles arhciving a contact us email.

        :param str name: The user's name.
        :param str message: The user's message.
        :param str email: The user's email.
        :rtype: ContactTable
        :return: The new contact message.
        """
        new_submission = Contact(
            name,
            email,
            message
        )

        exec_and_commit(db.session.add, new_submission)

        return new_submission
