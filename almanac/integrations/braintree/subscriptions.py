import logging
from braintree import Subscription
from braintree.exceptions import NotFoundError

from almanac.exc.exceptions import IntegrationException


class BraintreeSubscription(object):
    """
    Handles third-party integrations concerning subscripts for the braintree
    payment platform.
    """

    def start_subscription(self, unique_id, payment_method_token, plan_id):
        """
        Handles starting a subscription for the provided plan.

        :param str unique_id: A unique UUID associated with the subbscription.
        :param str payment_method_token: The payment method token which is
        created during customer creation.
        :param str plan_id: The plan we want the user to subscribe under
        :return: The result from starting the subscription
        """
        result = Subscription.create({
            'id': unique_id,
            'payment_method_token': payment_method_token,
            'plan_id': plan_id,
        })

        if not result.is_success:
            logging.error(
                'Failed to start subscription for payment method {0} '
                'with a plan ID of {1}',
                payment_method_token,
                plan_id,
            )
            raise IntegrationException('Failed to start subscription.')

        return result

    def stop_subscription(self, subscription_id):
        """
        Handles cancelling a subscription.

        :param str subscription_id: The unique subscription ID created from.
        :return: The result of stopping the subscription.
        """
        try:
            result = Subscription.cancel(subscription_id)
        except NotFoundError as e:
            logging.error('Subscription ID {0} not found.')
            raise IntegrationException(
                'Failed to cancel subscription. '
                'Please contact ian@ianleeclark.com'
            )

        if not result.is_success:
            logging.error(
                'Failed to cancel subscription by ID'
            )
            raise IntegrationException(
                'Failed to cancel subscription. '
                'Please contact ian@ianleeclark.com'
            )

        return result
