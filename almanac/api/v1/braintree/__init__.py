from .submerchant import export_routes as submerchant_routes
from .transaction import export_routes as transaction_routes
from .subscriptions import export_routes as subscription_routes


def export_all_routes(app):
    submerchant_routes(app)
    transaction_routes(app)
    subscription_routes(app)
