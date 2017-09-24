import logging
from http import HTTPStatus

from flask import jsonify
from flask.views import MethodView

from marshmallow.fields import String
from webargs.flaskparser import parser

from almanac.DAOs.braintree.subscription_dao import SubscriptionDAO
from almanac.exc.exceptions import EndpointException
from almanac.facades.braintree.subscription_facade import SubscriptionFacade
from almanac.schemas.return_schemas import SubscriptionMarshal
from almanac.utils.security import authentication_required


class Subscriptions(MethodView):
    """Braintree subscription management."""

    def __init__(self):
        self.sub_facade = SubscriptionFacade()
        self.sub_dao = SubscriptionDAO()

    @authentication_required
    def get(self, user_id):
        found_sub = self.sub_dao.get_subscription_by_user_id(user_id)

        logging.info(
            'Grabbed subscription for user {0} -- {1}'.format(
                user_id,
                found_sub,
            )
        )

        return jsonify(SubscriptionMarshal().dump(found_sub).data)

    @authentication_required
    def post(self, user_id):
        arg_fields = {
            'nonce': String(required=False),
            'first_name': String(required=False),
            'last_name': String(required=False),
        }
        args = parser.parse(arg_fields)

        if args.get('nonce') is not None:
            first_name = args.get('first_name')
            last_name = args.get('last_name')
            self._validate_first_and_last_name(first_name, last_name)

            new_sub = self.sub_facade.create_new_subscription_with_customer(
                user_id,
                args['nonce'],
                first_name,
                last_name,
            )
        else:
            new_sub = self.sub_facade.create_new_subscription(
                user_id,
            )

        logging.info(
            'Successfully created subscription for user {0}'.format(
                user_id,
            )
        )

        return jsonify(SubscriptionMarshal().dump(new_sub).data)

    @authentication_required
    def delete(self, user_id):
        sub_info = self.sub_facade.cancel_subscription(user_id)

        logging.info(
            'Cancelled subscription for user {0} -- {1}'.format(
                user_id,
                sub_info,
            )
        )

        return jsonify(SubscriptionMarshal().dump(sub_info).data)

    def _validate_first_and_last_name(self, first_name, last_name):
        if first_name == '' or first_name is None:
            raise EndpointException(
                'A first name must be provided.',
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )
        if last_name == '' or last_name is None:
            raise EndpointException(
                'A last name must be provided.',
                status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )


def export_routes(_app):
    _app.add_url_rule(
        '/braintree/<string:user_id>/subscriptions',
        view_func=Subscriptions.as_view('api_v1_braintree_subscriptions')
    )
