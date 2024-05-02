import jwt

from utils import database
from flask import request

class HTTPError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

def authenticate_student(config, connection):
    token = None

    header = request.headers.get("Authorization")
    if header:
        token = header.split(' ')[1]

    if not token:
        raise HTTPError(401, "Missing token.")

    try:
        token_data = jwt.decode(jwt=token, key=config['JWT']['SECRET_KEY'], algorithms=['HS256'])
        if token_data['admin'] is True:
            raise HTTPError(401, "Invalid token.")

        student = database.get_student_by_matric_num(connection, token_data['id'])
        if not student:
            raise HTTPError(401, "Invalid token.")

        return student
    except:
        raise HTTPError(401, "Invalid token.")

def authenticate_admin(config, connection):
    token = None

    header = request.headers.get("Authorization")
    if header:
        token = header.split(' ')[1]

    if not token:
        raise HTTPError(401, "Missing token.")

    try:
        token_data = jwt.decode(jwt=token, key=config['JWT']['SECRET_KEY'], algorithms=['HS256'])
        if token_data['admin'] is False:
            raise HTTPError(401, "Invalid token.")

        admin = database.get_admin_by_id(connection, token_data['id'])
        if not admin:
            raise HTTPError(401, "Invalid token.")

        return admin
    except:
        raise HTTPError(401, "Invalid token.")