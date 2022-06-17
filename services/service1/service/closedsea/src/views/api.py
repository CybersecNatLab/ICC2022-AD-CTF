import requests
from flask import Blueprint, request, abort, jsonify, current_app
from .helpers import login_user
from .exceptions import WrongPassword

api = Blueprint('api', 'api', url_prefix='/api')

@api.post('/login')
def api_login():
    if not request.is_json:
        abort(400)

    data = request.json
    try:
        username = data['username']
        password = data['password']
    except KeyError:
        abort(400)

    try:
        user_id, public_key = login_user(username, password)
    except WrongPassword:
        return abort(401)

    return jsonify({'username': username, 'public_key': public_key, 'user_id': user_id})
