import psycopg2
import psycopg2.extras

def connect_to_db(config):
    try:
        connection = psycopg2.connect(
            host=config["DATABASE"]["HOST"],
            user=config["DATABASE"]["USER"],
            password=config["DATABASE"]["PASSWORD"],
            dbname=config["DATABASE"]["DATABASE"],
        )

        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                name text NOT NULL,
                password text NOT NULL
                );
            """)

            connection.commit()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                code varchar(10) NOT NULL PRIMARY KEY,
                name text NOT NULL
                );
            """)

            connection.commit()

            cursor.execute("""
                INSERT INTO courses (code, name)
                VALUES ('CS', 'Computer Science'),
                    ('SE', 'Software Engineering'),
                    ('IT', 'Information Technology'),
                    ('CT', 'Computer Technology'),
                    ('CIS', 'Computer Information Systems')
                    ON CONFLICT (code) DO NOTHING;;
            """)

            connection.commit()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                matric_num varchar(10) NOT NULL PRIMARY KEY,
                password text NOT NULL,
                last_name text NOT NULL,
                first_name text NOT NULL,
                middle_name text,
                course varchar(10) NOT NULL,
                FOREIGN KEY (course) REFERENCES courses (code)
                );
            """)

            connection.commit()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                entry_date date NOT NULL,
                data text NOT NULL,
                student varchar(10) NOT NULL,
                FOREIGN KEY (student) REFERENCES students (matric_num)
                );
            """)

            connection.commit()

        return connection
    except Exception as e:
        print(e)
        raise

def create_student(connection, student):
    student_exists = get_student_by_matric_num(connection, student['matric_num'])
    if student_exists:
        return 0

    query = "INSERT INTO students(matric_num, password, first_name, last_name, middle_name, course) "\
            "VALUES (%s, %s, %s, %s, %s, "\
            "(SELECT code FROM courses WHERE name = %s)"\
            ");"

    values = (
        student['matric_num'],
        student['password'],
        student['first_name'],
        student['last_name'],
        student['middle_name'],
        student['course']
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values)

        connection.commit()
    except psycopg2.Error as error:
        raise error

def get_students(connection):
    query = "SELECT students.matric_num, students.first_name, students.last_name, students.middle_name, "\
            "courses.name as course_name FROM students "\
            "JOIN courses ON students.course = courses.code"

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query)

            return cursor.fetchall()
    except psycopg2.Error as error:
        raise error

def get_student_data(connection, matric_num):
    query = "SELECT students.matric_num, students.first_name, students.last_name, students.middle_name, "\
            "courses.name as course_name, "\
            "logs.id as id, logs.entry_date as entry_date, logs.data as data "\
            "FROM students "\
            "JOIN courses ON students.course = courses.code "\
            "JOIN logs ON students.matric_num = logs.student "\
            "WHERE students.matric_num = %s"

    values = (matric_num,)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchall()
    except psycopg2.Error as error:
        raise error

def get_student_by_matric_num(connection, matric_num):
    query = "SELECT students.matric_num, students.first_name, students.last_name, students.middle_name, "\
            "students.password, courses.name as course_name FROM students "\
            "JOIN courses ON students.course = courses.code "\
            "WHERE students.matric_num = %s"

    values = (matric_num,)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchone()
    except psycopg2.Error as error:
        raise error

def get_students_by_course(connection, course):
    query = "SELECT students.matric_num, students.first_name, students.last_name, students.middle_name, "\
            "courses.name as course_name FROM students "\
            "JOIN courses ON students.course = courses.code "\
            "WHERE courses.name LIKE %s"

    values = (f"%{course}%",)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchall()
    except psycopg2.Error as error:
        raise error

def get_students_by_name(connection, name):
    query = "SELECT students.matric_num, students.first_name, students.last_name, students.middle_name, "\
            "courses.name as course_name FROM students "\
            "JOIN courses ON students.course = courses.code "\
            "WHERE (students.first_name LIKE %s OR students.last_name LIKE %s OR students.middle_name LIKE %s)"

    values = (f"%{name}%", f"%{name}%", f"%{name}%")

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchall()
    except psycopg2.Error as error:
        raise error

def get_students_by_matric_num(connection, matric_num):
    query = "SELECT students.matric_num, students.first_name, students.last_name, students.middle_name, "\
            "courses.name as course_name FROM students "\
            "JOIN courses ON students.course = courses.code "\
            "WHERE students.matric_num LIKE %s"

    values = (f"%{matric_num}%",)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchall()
    except psycopg2.Error as error:
        raise error

def create_admin(connection, admin):
    cursor = connection.cursor()

    admin_exists = get_admin_by_name(connection, admin['name'])
    if admin_exists:
        return 0

    query = "INSERT INTO admins (name, password) "\
            "VALUES (%s, %s);"

    values = (admin['name'], admin['password'])

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
    except psycopg2.Error as error:
        raise error

    connection.commit()

def get_admin_by_id(connection, id):
    query = "SELECT * FROM admins WHERE id = %s"

    values = (id,)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchone()
    except psycopg2.Error as error:
        raise error

def get_admin_by_name(connection, name):
    query = "SELECT * FROM admins WHERE name = %s"

    values = (name,)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchone()
    except psycopg2.Error as error:
        raise error

def add_student_log(connection, log, matric_num):
    query = "INSERT INTO logs (entry_date, data, student) VALUES (%s, %s, %s)"

    values = (log['entry_date'], log['data'], matric_num)

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, values)
    except psycopg2.Error as error:
        raise error

    connection.commit()

def get_student_logs(connection, matric_num):
    query = "SELECT * FROM logs WHERE student = %s"

    values = (matric_num,)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchall()
    except psycopg2.Error as error:
        raise error

def get_student_log(connection, id):
    query = "SELECT * FROM logs WHERE id = %s"

    values = (id,)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)

            return cursor.fetchone()
    except psycopg2.Error as error:
        raise error

def delete_log(connection, id):
    log = get_student_log(connection, id)
    if not log:
        return 0

    query = "DELETE FROM logs WHERE id = %s"

    values = (id,)

    try:
        with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, values)
    except psycopg2.Error as error:
        raise error

    connection.commit()