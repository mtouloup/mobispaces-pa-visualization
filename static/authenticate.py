from flask import Flask, request, jsonify
from functools import wraps
import jwt
import requests
from flask_restx import Api, Resource


def require_token(view_func):
    @wraps(view_func)
    def decorator(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]

            try:
                validation_result = validate_jwt(token)
                if validation_result:
                    return view_func(*args, **kwargs)
                else:
                    return 'Invalid token', 403
            except jwt.ExpiredSignatureError:
                return 'Expired token', 403
            except jwt.InvalidTokenError:
                return 'Invalid token', 403

        return 'Missing token', 403

    return decorator


def validate_jwt(token):
    # Fetch the JWKS from the well-known URL
    jwks_url = 'https://mobispaces-keycloak.euprojects.net/auth/realms/Mobispaces'
    jwks_response = requests.get(jwks_url)
    jwks_response.raise_for_status()
    jwks_data = jwks_response.json()

    # Extract the public key from JWKS (assuming the first key in this example)
    cert_str = jwks_data['public_key']
    public_key = '-----BEGIN PUBLIC KEY-----\n' + cert_str + '\n-----END PUBLIC KEY-----'

    try:
        access_token_json = jwt.decode(token, public_key, algorithms=['RS256'], audience='account')
        return True
    except jwt.ExpiredSignatureError:
        return False
    except (jwt.InvalidTokenError, jwt.InvalidIssuerError):
        return False