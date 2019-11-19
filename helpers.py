import os
from functools import wraps
import psycopg2

from flask import redirect, session
from email_validator import validate_email, EmailNotValidError


def db_connection():
    try:
        db = psycopg2.connect(database=os.environ.get("DB"), user=os.environ.get("DB_USER"),
                              password=os.environ.get("DB_PASSWORD"),
                              host=os.environ.get("DB_HOST"), port=os.environ.get("DB_PORT"))
        connection = db.cursor()
    except psycopg2.InterfaceError:
            db.close()
            db = psycopg2.connect(database=os.environ.get("DB"), user=os.environ.get("DB_USER"),
                                  password=os.environ.get("DB_PASSWORD"),
                                  host=os.environ.get("DB_HOST"), port=os.environ.get("DB_PORT"))
            connection = db.cursor()
    return connection, db


def new_user(user):
    conn = db_connection()
    conn[0].execute("SELECT username from users where username = %s", (user,))
    row = conn[0].fetchone()
    if row is None:
        return True
    return False


def verify_input(input_text):
    alph = 0
    num = 0
    for i in input_text:
        if i.isalpha():
            alph = alph +1
        if i.isnumeric():
            num = num +1
    if alph > 0 and num > 0:
        return True
    return False


def verify_len(input_text, minimum, maximum):
    input_len = len(str(input_text))
    if minimum <= input_len <= maximum:
        return True
    return False


def verify_mail(email):
    try:
        validated = validate_email(email)
        if validated != EmailNotValidError:
            conn = db_connection()
            conn[0].execute("SELECT email from users where email = %s", (email,))
            row = conn[0].fetchone()
            if row is None:
                return "mail_new"
            return "mail_existed"
    except EmailNotValidError:
        return "mail_invalid"


def to_star(email_local):
    if len(str(email_local)) <= 3:
        return str("*"*len(str(email_local)))

    email_local_star = []
    for i in range(0, 2):
        email_local_star.append(email_local[i])
    for i in range(2, len(str(email_local))-1):
        email_local_star.append("*")
    email_local_star.append(email_local[-1])
    email_star = "".join(email_local_star)
    return email_star


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/welcome")
        return function(*args, **kwargs)
    return decorated_function
