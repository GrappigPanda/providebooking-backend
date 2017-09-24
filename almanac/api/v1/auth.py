import logging

from flask import Response, jsonify
from flask.views import MethodView
from flask import current_app as app
from marshmallow.fields import String
from webargs.flaskparser import parser

from almanac.DAOs.auth_dao import AuthDAO
from almanac.schemas.return_schemas import UserMarshal
from almanac.utils.security import create_token


class Authentication(MethodView):
    """Houses authentication endpoints."""

    def post(self):
        arg_fields = {
            'user_challenge': String(required=True),
            'plaintext_password': String(required=True),
        }
        args = parser.parse(arg_fields)

        user_info = AuthDAO().login(**args)

        logging.info('Succesfully validated incoming user {0}'.format(
            args['user_challenge']
        ))

        # type: Response
        response = jsonify(
            {
                'new_jwt': create_token(
                    str(user_info.public_id),
                    app.config
                ).decode('utf-8'),
                'user_info': UserMarshal().dump(user_info).data,
            }
        )

        return response


def export_routes(_app):
    _app.add_url_rule(
        '/authentication/login',
        view_func=Authentication.as_view('api_v1_authentication')
    )