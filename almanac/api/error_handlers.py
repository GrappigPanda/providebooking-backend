import http

from flask import current_app as app, jsonify

from almanac.exc.exceptions import BaseAlmanacException


def register_error_handlers(_app):
    @_app.errorhandler(BaseAlmanacException)
    def handle_all_errors(e):
        response = jsonify({'msg': e.msg})
        response.status_code = e.status_code
        return response