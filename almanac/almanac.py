import braintree
from os import environ
from flask import Flask
from flask_cors import CORS

from almanac.models import db
from almanac.api.v1.schedules import export_routes as exp_schedules
from almanac.api.v1.addresses import export_routes as exp_addresses
from almanac.api.v1.users import export_routes as exp_users
from almanac.api.v1.users_reset_password import export_routes as exp_reset_pw
from almanac.api.v1.events import export_routes as exp_events
from almanac.api.v1.auth import export_routes as exp_auth
from almanac.api.v1.contact_form import export_routes as exp_contact_form
from almanac.api.v1.braintree import export_all_routes as exp_braintree

def create_app(config_filename):
    app = Flask(__name__)
    CORS(app)
    app.config['JWT_KEY'] = environ['KRONIKL_JWT_KEY'] or 'testsecretkey'
    app.config['JWT_EXPIRATION'] = environ['KRONIKL_JWT_EXPIRATION'] or 10
    app.config['TESTING'] = False
    app.config['ENVIRONMENT'] = 'Dev'

    if app.config['ENVIRONMENT'] == 'Dev':
        app.config['SQLALCHEMY_DATABASE_URI'] = environ['KRONIKL_POSTGRES_FQDN']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        braintree.Configuration.configure(
            environment=braintree.Environment.Sandbox,
            merchant_id='<merchant_id>',
            public_key='<public_key>',
            private_key='<private_key>',
        )
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = environ['KRONIKL_POSTGRES_FQDN']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        environment = None
        if environ['KRONIKL_BRAINTREE_ENVIRONMENT'] == 'sandbox':
            environment = braintree.Environment.Sandbox
        else:
            environment = braintree.Environment.Production

        braintree.Configuration.configure(
            environment=environment,
            merchant_id=environ['KRONIKL_BRAINTREE_MERCHANT_ID'],
            public_key=environ['KRONIKL_BRAINTREE_PUBLIC_KEY'],
            private_key=environ['KRONIKL_BRAINTREE_PRIVATE_KEY'],
        )

    # Unit test variable that dictates if we tear down database tables after
    # running the tests.
    app.config['TEAR_DOWN_AFTER'] = True

    with app.app_context():
        from almanac.api.error_handlers import register_error_handlers
        from almanac.api.lifecycle_handlers import start_lifecycle_hooks

        register_error_handlers(app)
        start_lifecycle_hooks(app)

        exp_users(app)
        exp_schedules(app)
        exp_events(app)
        exp_auth(app)
        exp_contact_form(app)
        exp_addresses(app)
        exp_reset_pw(app)

        # Execute routes for nested directories.
        exp_braintree(app)

    db.init_app(app)
    db.app = app

    return app

app = create_app(None)
