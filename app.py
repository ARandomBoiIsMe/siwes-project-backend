import os
import jwt

from datetime import datetime, timedelta, UTC
from flask import Flask, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from utils import database, config
from utils.authentication import authenticate_admin, authenticate_student, HTTPError

CONFIG = config.load_config()
CONNECTION = database.connect_to_db(CONFIG)

app = Flask(__name__)

@app.post("/student/register")
def register_student():
    student = request.get_json()

    if (
        not student.get('matric_num') or not student.get('password') or not student.get('first_name') or
        not student.get('last_name') or not student.get('course')
    ):
        return jsonify({"message": "Incomplete student data."}), 400

    student['middle_name'] = student.get('middle_name')

    student['password'] = generate_password_hash(student['password'], 'scrypt')

    response = database.create_student(CONNECTION, student)
    if response == 0:
        return jsonify({"message": "This student already has an account on this platform."}), 409

    return jsonify({"message": "Student registered successfully."}), 200

@app.post("/student/login")
def login_student():
    data = request.get_json()

    if not data.get('matric_num') or not data.get('password'):
        return jsonify({"message": "Incomplete credentials."}), 400

    student = database.get_student_by_matric_num(CONNECTION, data['matric_num'])
    if not student:
        return jsonify({"message": "Invalid credentials."}), 401

    if not check_password_hash(student['password'], data['password']):
        return jsonify({"message": "Invalid credentials."}), 401

    payload = {
        'id': student['matric_num'],
        'admin': False,
        'exp': datetime.now(UTC) + timedelta(minutes=60)
    }

    token = jwt.encode(payload=payload, key=CONFIG['JWT']['SECRET_KEY'], algorithm="HS256")
    return jsonify({'token' : token})

@app.post('/logs')
def add_log():
    try:
        student = authenticate_student(CONFIG, CONNECTION)

        log = request.get_json()
        if not log.get('entry_date') or not log.get('data'):
            return jsonify({"message": "Incomplete log data."}), 400

        matric_num = student['matric_num']

        database.add_student_log(CONNECTION, log, matric_num)

        return jsonify({'message': 'Log added successfully.'}), 200
    except HTTPError as error:
        return jsonify({'message': error.message}), error.code

@app.get('/logs')
def student_logs():
    try:
        student = authenticate_student(CONFIG, CONNECTION)

        matric_num = student['matric_num']
        logs = database.get_student_logs(CONNECTION, matric_num)

        response = {
            'logs': [
                {
                    'id': log['id'],
                    'entry_date': log['entry_date'],
                    'data': log['data']
                } for log in logs
            ]
        }

        return jsonify(response), 200
    except HTTPError as error:
        return jsonify({'message': error.message}), error.code

@app.get('/log/<id>')
def student_log(id):
    try:
        authenticate_student(CONFIG, CONNECTION)

        log = database.get_student_log(CONNECTION, id)
        if not log:
            return jsonify({"message": "Log not found."}), 404

        response = {
            'log': {
                'id': log['id'],
                'entry_date': log['entry_date'],
                'data': log['data']
            }
        }

        return jsonify(response), 200
    except HTTPError as error:
        return jsonify({'message': error.message}), error.code

@app.delete('/log/<id>')
def delete_log(id):
    try:
        authenticate_student(CONFIG, CONNECTION)

        response = database.delete_log(CONNECTION, id)
        if response == 0:
            return jsonify({"message": "Log not found."}), 404

        return jsonify({'message': 'Log deleted successfully.'}), 200
    except HTTPError as error:
        return jsonify({'message': error.message}), error.code

@app.post("/admin/register")
def register_admin():
    admin = request.get_json()

    if not admin.get('name') or not admin.get('password'):
        return jsonify({"message": "Incomplete admin data."}), 400

    admin['password'] = generate_password_hash(admin['password'], 'scrypt')

    response = database.create_admin(CONNECTION, admin)
    if response == 0:
        return jsonify({"message": "This admin already has an account on this platform."}), 409

    return jsonify({"message": "Admin registered successfully."}), 200

@app.post("/admin/login")
def login_admin():
    data = request.get_json()

    if not data.get('name') or not data.get('password'):
        return jsonify({"message": "Incomplete credentials."}), 400

    admin = database.get_admin_by_name(CONNECTION, data['name'])
    if not admin:
        return jsonify({"message": "Invalid credentials."}), 401

    if not check_password_hash(admin['password'], data['password']):
        return jsonify({"message": "Invalid credentials."}), 401

    payload = {
        'id': admin['id'],
        'admin': True,
        'exp': datetime.now(UTC) + timedelta(minutes=60)
    }

    token = jwt.encode(payload=payload, key=CONFIG['JWT']['SECRET_KEY'], algorithm="HS256")
    return jsonify({'token' : token})

@app.get('/students')
def get_students():
    try:
        authenticate_admin(CONFIG, CONNECTION)

        if not request.args:
            students = database.get_students(CONNECTION)

            response = {
                'students': [
                    {
                        'matric_num': student['matric_num'],
                        'last_name': student['last_name'],
                        'first_name': student['first_name'],
                        'middle_name': student['middle_name'],
                        'course': student['course_name']
                    } for student in students
               ]
            }

            return jsonify(response), 200

        attribute = request.args.get('attribute')
        value = request.args.get('value')

        if not attribute or not value:
            return jsonify({"message": "Incomplete request data."}), 400

        if attribute == 'name':
            students = database.get_students_by_name(CONNECTION, value)
        elif attribute == 'course':
            students = database.get_students_by_course(CONNECTION, value)
        elif attribute == 'matric_num':
            students = database.get_students_by_matric_num(CONNECTION, value)
        else:
            return jsonify({"message": "Incorrect request format."}), 400

        response = {
            'students': [
                {
                    'matric_num': student['matric_num'],
                    'last_name': student['last_name'],
                    'first_name': student['first_name'],
                    'middle_name': student['middle_name'],
                    'course': student['course_name']
                } for student in students
            ]
        }

        return jsonify(response), 200
    except HTTPError as error:
        return jsonify({'message': error.message}), error.code

@app.get('/student/<matric_num>')
def get_student_data(matric_num):
    try:
        authenticate_admin(CONFIG, CONNECTION)

        matric_num = matric_num.replace('-', '/')

        student = database.get_student_by_matric_num(CONNECTION, matric_num)
        if not student:
            return jsonify({'message': 'Student does not exist.'}), 404

        student_logs = database.get_student_logs(CONNECTION, matric_num)

        response = {
            'student': {
                'matric_num': student['matric_num'],
                'last_name': student['last_name'],
                'first_name': student['first_name'],
                'middle_name': student['middle_name'],
                'course': student['course_name'],
                'logs': [
                    {
                        'id': log['id'],
                        'entry_date': log['entry_date'],
                        'data': log['data']
                    } for log in student_logs
                ]
            }
        }

        return jsonify(response), 200
    except HTTPError as error:
        return jsonify({'message': error.message}), error.code

@app.get('/student/<matric_num>/log/<id>')
def get_student_log(matric_num, id):
    try:
        authenticate_admin(CONFIG, CONNECTION)

        matric_num = matric_num.replace('-', '/')

        student = database.get_student_by_matric_num(CONNECTION, matric_num)
        if not student:
            return jsonify({'message': 'Student does not exist.'}), 404

        student_log = database.get_student_log(CONNECTION, id)
        if not student_log:
            return jsonify({'message': 'Log does not exist.'}), 404

        response = {
            'log': {
                'id': student_log['id'],
                'entry_date': student_log['entry_date'],
                'data': student_log['data']
            }
        }

        return jsonify(response), 200
    except HTTPError as error:
        return jsonify({'message': error.message}), error.code

if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=os.environ.get('PORT') or 4000
    )