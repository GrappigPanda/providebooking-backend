from braintree import WebhookNotification


def bt_webhook_parser(request):
    """
    Takes a flask request and

    :param flask.request request: The request object.
    :rtype: WebhookNotification
    :return: The parsed webhook notification.
    """
    return WebhookNotification.parse(
        str(request.form['bt_signature']),
        str(request.form['bt_payload']),
    )