import logging
import sqlalchemy
from sqlalchemy.exc import IntegrityError

from almanac.exc.exceptions import SQLException
from almanac.models import db


def exec_and_commit(f, obj, *, skip_commit=False):
    """
    A helper method to exec a sql statement and commit.

    :param function f: The function to execute.
    :param object obj: The SQL object to create.
    :param bool skip_commit: Tells if we need to insert but not commit.
    :raises: SQLException
    :rtype: NoneType
    :return:
    """
    try:
        f(obj)
        if not skip_commit:
            db.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        logging.error('Failed to commit object {0} due to '
                      'exception {1}'.format(
            obj,
            e,
        ))

        raise SQLException('Error processing request.')
