from flask import request, g
from functools import wraps
import jwt
import requests
from jwcrypto import jwk

def require_token(view_func):
    @wraps(view_func)
    def decorator(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        token_status = "valid"  # Possible values: "valid", "invalid", "missing"

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split('Bearer ')[1]

            try:
                validation_result, role = validate_jwt(token)
                if validation_result:
                    g.user_role = role
                    token_status = "valid"
                else:
                    token_status = "invalid"
                    g.user_role = "none"
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                token_status = "invalid"
                g.user_role = "none"
        else:
            token_status = "missing"
            g.user_role = "none"

        g.token_status = token_status
        return view_func(*args, **kwargs)
        
    return decorator


# This function validates a JWT token using the JWKS URL of the authorization server
def validate_jwt(token):
    
    # Fetch the JWKS from the well-known URL
    jwks_url = 'https://mobispaces-keycloak.euprojects.net/auth/realms/Mobispaces/protocol/openid-connect/certs'
    jwks_response = requests.get(jwks_url)
    jwks_response.raise_for_status()
    
    jwks_data = jwks_response.json()
    token_header = jwt.get_unverified_header(token)

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

        realm_access_roles = access_token_json.get('realm_access', {}).get('roles', [])
        
        # Iterate through the roles and skip 'offline_access'
        for role in realm_access_roles:
            if role != "offline_access":
                return True, role  # Return the first non-'offline_access' role

        # No suitable role found (either 'offline_access' is the only role or the list is empty)
        return False, None
    
    except jwt.ExpiredSignatureError:
        return False
    except (jwt.InvalidTokenError, jwt.InvalidIssuerError) as e:
        print(f"Invalid token or issuer error: {e}", flush=True)
        return False