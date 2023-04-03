from trino.auth import JWTAuthentication
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import  text

import requests

def get_access_token(username, password, client_id, client_secret, realm):
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': client_id,
        'client_secret': client_secret
    }
    url = 'https://mobispaces-keycloak.euprojects.net/auth/realms/'+realm+'/protocol/openid-connect/token'
    response = requests.post(url, data=data)
    response.raise_for_status()
    access_token = response.json()['access_token']
    return access_token


access_token = get_access_token('xxx', 'xxx', 'trino-coordinator', '6ldKEV80oBgiVu5pomys2j0HRjAnrhfC', 'Mobispaces')


engine = create_engine(
    "trino://mobispaces-trino.euprojects.net:443/mongo",
    connect_args={
        "auth": JWTAuthentication(access_token),   # insert authorization token after keycloak login
        "http_scheme": "https",
    }
)
connection = engine.connect()

# dummy test db and collection
rows = connection.execute(text("SELECT * FROM testdb.test")).fetchall()




print(access_token)
print(rows)