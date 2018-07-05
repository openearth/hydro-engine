'''Application error handlers.'''
from flask import Blueprint, jsonify

import traceback

error_handler = Blueprint('errors', __name__)


@error_handler.app_errorhandler(Exception)
def handle_unexpected_error(error):
    stack = traceback.format_exc()

    status_code = 500
    success = False
    response = {
        'success': success,
        'error': {
            'type': 'UnexpectedException',
            'message': str(error),
            'stack': stack
        }
    }

    return jsonify(response), status_code
