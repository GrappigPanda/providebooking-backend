import logging

from flask import jsonify
from flask.views import MethodView
from marshmallow import validate
from marshmallow.fields import Boolean, Int, String
from webargs.flaskparser import parser

from almanac.DAOs.address_dao import AddressDAO
from almanac.schemas.return_schemas import AddressMarshal
from almanac.utils.security import authentication_required


class Addresses(MethodView):
    """Houses CRUD operations for address management."""

    @authentication_required
    def get(self, user_id, address_id):
        address = AddressDAO().get_by_public_id(address_id, user_id)

        logging.info(
            'Retrieved address {0} for user ID {1}'.format(
                address,
                user_id
            )
        )

        return jsonify(AddressMarshal().dump(address).data)

    @authentication_required
    def put(self, user_id, address_id):
        arg_fields = {
            'first_name': String(),
            'last_name': String(),
            'street_address': String(),
            'locality': String(),
            'region': String(),
            'postal_code': String(),
            'country_code_alpha2': String(
                validate=validate.Length(2)
            ),
            'is_default': Boolean(),
            'extended_address': String()
        }
        args = parser.parse(arg_fields)
        for k, v in args.items():
            if v is None:
                del args[k]

        address = AddressDAO().update_address(address_id, user_id, **args)

        logging.info(
            'Updated address ID {0} for user {1}. Got back {2}'.format(
                address_id,
                user_id,
                address
            )
        )

        return jsonify(AddressMarshal().dump(address).data)

    @authentication_required
    def delete(self, user_id, address_id):
        address = AddressDAO().delete_address(address_id, user_id)

        logging.info(
            'Deleted address ID {0} for user {1}. Got back {2}.'.format(
                address_id,
                user_id,
                address_id
            )
        )

        return jsonify(AddressMarshal().dump(address).data)


class DefaultAddress(MethodView):
    """
    Handles retrieving attributes from an address (mostly is_default).
    """

    @authentication_required
    def get(self, user_id):
        address = AddressDAO().get_default_for_user(user_id)

        logging.info(
            'Retrieved default address {0} for user ID {1}'.format(
                address,
                user_id
            )
        )

        return jsonify(AddressMarshal().dump(address).data)


class AllAddresses(MethodView):
    """
    Handles retrieving attributes from an address (mostly is_default).
    """

    @authentication_required
    def get(self, user_id):
        address = AddressDAO().get_all_addresses_for_user(user_id)

        logging.info(
            'Retrieved all addresses {0} for user ID {1}'.format(
                address,
                user_id
            )
        )

        return jsonify(
            {'addresses': AddressMarshal(many=True).dump(address).data}
        )


class AddressMutation(MethodView):

    @authentication_required
    def post(self, user_id):
        arg_fields = {
            'first_name': String(required=True),
            'last_name': String(required=True),
            'street_address': String(required=True),
            'locality': String(required=True),
            'region': String(required=True),
            'postal_code': String(required=True),
            'country_code_alpha2': String(
                required=True,
                validate=validate.Length(2)
            ),
            'is_default': Boolean(required=True, default=False, missing=False),
            'extended_address': String()
        }
        args = parser.parse(arg_fields)

        address = AddressDAO().create_address(user_id, **args)

        logging.info(
            'Successfully created new address {0} for user {1}.'.format(
                address,
                user_id
            )
        )

        return jsonify(AddressMarshal().dump(address).data)


def export_routes(_app):
    _app.add_url_rule(
        '/users/<string:user_id>/addresses/<string:address_id>',
        view_func=Addresses.as_view('api_v1_addresses')
    )

    _app.add_url_rule(
        '/users/<string:user_id>/addresses/default',
        view_func=DefaultAddress.as_view('api_v1_default_address')
    )

    _app.add_url_rule(
        '/users/<string:user_id>/addresses/',
        view_func=AllAddresses.as_view('api_v1_all_addresses')
    )

    _app.add_url_rule(
        '/users/<string:user_id>/address',
        view_func=AddressMutation.as_view('api_v1_create_address')
    )

