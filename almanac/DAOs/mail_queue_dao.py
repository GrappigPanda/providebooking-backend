from almanac.DAOs.base_dao import BaseDAO
from almanac.models import db
from almanac.models.email_queue_table import EmailQueueTable as Email
from almanac.utils.database_utils import exec_and_commit


class MailQueueDAO(BaseDAO):
    """
    Handles adding mail to the mail queue
    """

    def push_to_queue(self, email_to, email_from, subject, body):
        """
        Handles adding a new email to the mail queue.

        :param str email_to: The email we'll be mailing.
        :param str email_from: The origin email.
        :param str subject: The subject line of the email.
        :param str body: The body of the email message.
        :rtype: EmailQueueTable
        :return: The newly pushed email.
        """
        new_email = Email(
            email_to,
            email_from,
            subject,
            body
        )

        exec_and_commit(db.session.add, new_email)

        return new_email
