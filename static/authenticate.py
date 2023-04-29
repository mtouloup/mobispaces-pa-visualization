from flask import request
from functools import wraps
import jwt
import requests
from jwcrypto import jwk

# This decorator function checks if a valid token is present in the request header
def require_token(view_func):
    @wraps(view_func)
    def decorator(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]

            try:
                print("Before calling validate_jwt inside decorator", flush=True)
                validation_result = validate_jwt(token)
                print("After calling validate_jwt inside decorator", flush=True)

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

# This function validates a JWT token using the JWKS URL of the authorization server
def validate_jwt(token):
    # Fetch the JWKS from the well-known URL
    jwks_url = 'https://mobispaces-keycloak.euprojects.net/auth/realms/Mobispaces/protocol/openid-connect/certs'
    jwks_response = requests.get(jwks_url)
    jwks_response.raise_for_status()

    jwks_data = jwks_response.json()
    token_header = jwt.get_unverified_header(token)
    print(f"Token header: {token_header}", flush=True)

    # Find the matching JWK in the JWKS using the 'kid' field
    matching_jwk = None
    for jwk_data in jwks_data['keys']:
        if jwk_data['kid'] == token_header['kid']:
            matching_jwk = jwk_data
            break

    if not matching_jwk:
        print("No matching JWK found in the JWKS", flush=True)
        return False

    # Convert the JWK to a PEM format public key
    public_key = jwk.JWK(**matching_jwk).export_to_pem()

    # Verify the JWT token using the public key
    try:
        access_token_json = jwt.decode(token, public_key, algorithms=[token_header['alg']], audience='account')
        return True
    except jwt.ExpiredSignatureError:
        return False
    except (jwt.InvalidTokenError, jwt.InvalidIssuerError) as e:
        print(f"Invalid token or issuer error: {e}",flush=True)
        return False