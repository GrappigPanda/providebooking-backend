import logging
from http import HTTPStatus

from braintree import WebhookNotification
from flask import jsonify, request
from flask.views import MethodView
from marshmallow import validate

from marshmallow.fields import String, DateTime, Boolean
from webargs.fields import Nested
from webargs.flaskparser import parser

from almanac.DAOs.braintree.merchant_dao import MerchantDAO
from almanac.api.v1.utils.webhooks import bt_webhook_parser
from almanac.exc.exceptions import EndpointException
from almanac.facades.braintree.submerchant_facade import SubmerchantFacade
from almanac.utils.security import authentication_required


class Submerchants(MethodView):
    """Braintree submerchant management."""

    @authentication_required
    def post(self, user_id):
        arg_fields = {
            'individual': Nested({
                'first_name': String(required=True),
                'last_name': String(required=False),
                'email': String(required=True),
                'phone': String(),
                # TODO(ian): Do we need to assert this is > 18 years old?
                'date_of_birth': DateTime(required=True),
                'address': Nested({
                    'street_address': String(required=True),
                    'locality': String(required=True),
                    'region': String(required=True),
                    'postal_code': String(required=True)
                }, required=True)
            }),

            # NOTE: Business is only required if requesting user is
            # registering on behalf of a business.
            'business': Nested({
                'legal_name': String(required=True),
                'dba_name': String(required=True),
                # TODO(ian): Only required if `legal_name` is added above.
                'tax_id': String(required=True),
                'address': Nested({
                    'street_address': String(required=True),
                    'locality': String(required=True),
                    'region': String(required=True),
                    'postal_code': String(required=True)
                })
            }),

            'funding': Nested({
                # TODO(ian): Set something here. The name of my company?
                'descriptor': String(
                    missing=''
                ),
                'account_number': String(required=True),
                'routing_number': String(required=True),
            }),

            'tos_accepted': Boolean(
                required=True,
                default=False,
                missing=False,
                validate=validate.OneOf([True])
            ),

            'register_as_business': Boolean(
                required=True,
                default=False,
                missing=False,
            )
        }
        args = parser.parse(arg_fields)

        if args['register_as_business'] and args.get('business') is None:
            raise EndpointException(
                'Whenever registering as a business, business information '
                'must be supplied.'
            )

        SubmerchantFacade().create_submerchant(args, user_id)

        logging.info(
            'Successfully created submerchant for email {0} on User '
            '{1}.'.format(
                args['individual']['email'],
                user_id
            )
        )

        return jsonify({'success': True})


class WebhookHandler(MethodView):

    def post(self):
        parsed_request = bt_webhook_parser(request)
        MerchantDAO().set_approved_or_declined(parsed_request)

        return jsonify({'success': True})


def export_routes(_app):
    _app.add_url_rule(
        '/braintree/<string:user_id>/submerchant',
        view_func=Submerchants.as_view('api_v1_braintree_submerchant')
    )

    _app.add_url_rule(
        '/braintree/submerchant/webhook',
        view_func=WebhookHandler.as_view('api_v1_submerchant_webhook')
    )
