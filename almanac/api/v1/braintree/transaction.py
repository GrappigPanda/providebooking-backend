from flask import jsonify
from flask.views import MethodView
from braintree import ClientToken

import braintree

from almanac.utils.security import authentication_required


class GenerateClientToken(MethodView):
    """Generates a client token to be used whenever using the Paypal API."""
    def post(self, user_id):
        return jsonify({'token': self._generate_token()})

    @authentication_required
    def _generate_token(self):
        braintree.Configuration.configure(
            braintree.Environment.Sandbox,
            'sgppp5zt6vjkd3nx',
            'jbbsgnnp7dfk3yt7',
            'd8a1a6ce8de596691be3d0d18678d095'
        )
        return ClientToken.generate()


def export_routes(_app):
    _app.add_url_rule(
        '/braintree/<string:user_id>/generate_token',
        view_func=GenerateClientToken.as_view('api_v1_braintree_client_token')
    )
