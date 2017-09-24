from flask import jsonify
from flask.views import MethodView

from marshmallow.fields import String, Email
from webargs.flaskparser import parser

from almanac.facades.contact_facade import ContactFacade


class Contacts(MethodView):
    """Allows contact form submission."""

    def post(self):
        arg_fields = {
            'name': String(required=True),
            'email': Email(required=True),
            'message': String(required=True)
        }
        args = parser.parse(arg_fields)

        ContactFacade().add_new_contact_message(
            args['name'],
            args['email'],
            args['message'],
        )

        return jsonify({'success': True})


def export_routes(_app):
    _app.add_url_rule(
        '/contact',
        view_func=Contacts.as_view('api_v1_contact_form')
    )