import logging
import pytz
from flask.views import MethodView
from flask import jsonify
from marshmallow import validate

from marshmallow.fields import String, Float
from webargs.flaskparser import parser

from almanac.DAOs.user_dao import UserDAO
from almanac.exc.exceptions import EndpointException
from almanac.facades.user_facade import UserFacade
from almanac.schemas.return_schemas import UserMarshal
from almanac.utils.security import authentication_required


class Users(MethodView):
    """Houses CRUD operations for user management."""

    @authentication_required
    def get(self, user_id):
        user_info = UserFacade().get_user_by_id(user_id)

        logging.info('Retrieved user info for {0}'.format(user_id))

        return jsonify(UserMarshal().dump(user_info).data)

    def post(self):
        arg_fields = {
            'email': String(required=True),
            'username': String(required=True, max=32),
            'plaintext_password': String(required=True),
            'local_tz': String(
                required=True,
                validate=validate.OneOf(pytz.all_timezones
            )),
        }
        args = parser.parse(arg_fields)

        try:
            user_info = UserFacade().create_user(
                args['email'],
                args['plaintext_password'],
                args['local_tz'],
                args['username']
            )
        except Exception as e:
            logging.error(
                'Random exception encountered registering user {0}'.format(e)
            )
            raise EndpointException('Failed to register user.')

        logging.info('Successfully created new user at {0}'.format(
            args['email']
        ))

        return jsonify(UserMarshal().dump(user_info).data)

    @authentication_required
    def delete(self, user_id):
        user_info = UserDAO().delete(
            user_id
        )

        logging.info(
            'Successfully deleted user {0} for requesting user.'.format(
                user_id
            )
        )

        return jsonify(UserMarshal().dump(user_info).data)


class GetUserByEmail(MethodView):
    """Handles retrieving a user by email"""

    @authentication_required
    def get(self, email):
        user_info = UserFacade().get_user_by_email(email)

        logging.info('Succesfully retrieved user by email {0}'.format(email))

        return jsonify(UserMarshal().dump(user_info).data)


class UserPreferences(MethodView):
    """Houses CRUD operations for user preference management."""

    @authentication_required
    def put(self, user_id):
        arg_fields = {
            'email': String(),

            # NOTE: If plaintext_password is provided, current_password must
            # also be provided.
            'plaintext_password': String(),
            'current_password': String(),

            'five_min_price': Float(),
            'fifteen_min_price': Float(),
            'thirty_min_price': Float(),
            'sixty_min_price': Float(),
        }
        args = parser.parse(arg_fields)

        user_info = UserDAO().put(
            user_id,
            **args
        )

        logging.info('Successfully updated {0} for user {1}'.format(
            args.keys(),
            user_id
        ))

        return jsonify(UserMarshal().dump(user_info).data)


class VerificationToken(MethodView):
    """
    Handles anything related to the verification token.
    """

    def post(self):
        arg_fields = {
            'token': String(required=True),
        }
        args = parser.parse(arg_fields)

        validated_user = UserDAO().verify_token(args['token'])

        logging.info(
            'Successfully validated token {0} for user {1}.'.format(
                args['token'],
                validated_user,
            )
        )

        return jsonify(UserMarshal().dump(validated_user).data)

    def put(self):
        arg_fields = {
            'email': String(required=True),
        }
        args = parser.parse(arg_fields)

        UserFacade().regenerate_verification_token(args['email'])

        logging.info('Successfully regenerated token')

        return jsonify({'success': True})


def export_routes(_app):
    _app.add_url_rule(
        '/users/<string:user_id>/preferences',
        view_func=UserPreferences.as_view('api_v1_users_preferences')
    )

    _app.add_url_rule(
        '/users/<string:user_id>',
        view_func=Users.as_view('api_v1_users_update_user'),
        methods=['GET', 'DELETE']
    )

    _app.add_url_rule(
        '/users/',
        view_func=Users.as_view('api_v1_users_new_user'),
        methods=['POST']
    )

    _app.add_url_rule(
        '/users/email/<string:email>',
        view_func=GetUserByEmail.as_view('api_v1_users_get_by_email'),
        methods=['GET']
    )

    _app.add_url_rule(
        '/users/verify',
        view_func=VerificationToken.as_view('api_v1_users_verification'),
        methods=['POST', 'PUT']
    )

