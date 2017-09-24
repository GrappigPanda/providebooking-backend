from flask import g
from datetime import datetime, timedelta
from functools import wraps

import jwt
import logging

from almanac.DAOs.user_dao import UserDAO
from almanac.exc.exceptions import SecurityException


def create_token(user_id, app_config):
    return jwt.encode({
        'user_id': user_id,
        'issuance': str(datetime.utcnow()),
        'expiration': str(datetime.utcnow() + timedelta(
            minutes=int(app_config['JWT_EXPIRATION'])
        ))},
        app_config['JWT_KEY']
    )


def authentication_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if kwargs.get('user_id', False):
            return __authorize_uri(f, args, kwargs)
        if kwargs.get('email', False):
            user = UserDAO().get_by_email(kwargs['email'])
            return __authorize_uri(f, args, kwargs, user_id=user.public_id)
    return wrapper


def __authorize_uri(f, args, kwargs, *, user_id=None):
    if user_id is not None:
        if user_id == g.user_info['user_id']:
            return f(*args, **kwargs)

    if kwargs.get('user_id') == g.user_info['user_id']:
        return f(*args, **kwargs)
    else:
        logging.error(
            'Failed to authorize incoming access request to {0} for'
            ' jwt {1} and URI user_id {2} | email {3}'.format(
                f,
                g.user_info,
                kwargs.get('user_id'),
                kwargs.get('email'),
            )
        )
        raise SecurityException('Failed to authorize incoming request.')

