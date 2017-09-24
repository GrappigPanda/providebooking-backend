from http import HTTPStatus

import logging
import jwt

from flask import current_app as app, request, g

from almanac.exc.exceptions import HookException


def start_lifecycle_hooks(_app):
    @_app.before_request
    def process_jwt_token():
        logging.info('{0}-{1}-2'.format(request.url_rule, request.method, request.url))
        if 'authentication/login' in request.url:
            pass
        elif request.url.endswith('/users/') and request.method == 'POST':
            pass
        elif '/users/reset_password' in request.url:
            pass
        elif '/users/verify' in request.url:
            pass
        elif 'webhook' in request.url and request.method == 'POST':
            pass
        elif request.method not in ['POST', 'GET', 'PUT', 'DELETE']:
            pass
        elif not app.config['TESTING']:
            token = request.headers.get(
                'jwt',
                None
            )

            if token is None:
                raise HookException(
                    "Failed to get JWT token in request.",
                    HTTPStatus.UNAUTHORIZED
                )

            try:
                g.user_info = jwt.decode(token, app.config['JWT_KEY'])

            except jwt.ExpiredSignatureError as e:
                logging.error(e)

                raise HookException(
                    'Session has expired. Please login.',
                    HTTPStatus.UNAUTHORIZED
                )

            except jwt.DecodeError as e:
                logging.error(e)

                raise HookException(
                    'Session has expired. Please login.',
                    HTTPStatus.UNAUTHORIZED
                )
