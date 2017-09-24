import os

from almanac.DAOs.contact_dao import ContactUsDAO
from almanac.DAOs.mail_queue_dao import MailQueueDAO


class ContactFacade(object):
    """
    Handles anything necessary to the "contact us" from.
    """

    def add_new_contact_message(self, name, email, message):
        """
        Handles adding a new "contact us" form message and adding it to our
        email queue.

        :param str name: The user's name.
        :param str message: The user's message.
        :param str email: The user's email.
        :rtype: ContactTable
        :return: The newly created contact message.
        """
        new_message = ContactUsDAO().add_new_contact_message(
            name,
            message,
            email
        )

        MailQueueDAO().push_to_queue(
            os.environ["KRONIKL_EMAIL_FORWARD_TO"],
            new_message.email,
            "New contact form submission - {0}".format(new_message.email),
            new_message.message
        )