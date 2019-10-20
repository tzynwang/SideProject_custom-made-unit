import json
import os
import psycopg2
import requests
import urllib.parse

from functools import wraps
from flask import redirect, render_template, request, session
from flask_mail import Mail, Message
from flask_session import Session
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from email_validator import validate_email, EmailNotValidError


conn = psycopg2.connect(database="d4si1co4s3p2gi", user="mjyufuhmpotxwl", 
                        password="308d87d49fb8710befb9df22342570abaf26a0b16a3ab24fab0a87796f984943", 
                        host="ec2-174-129-218-200.compute-1.amazonaws.com", port="5432")
connection = conn.cursor()


def ApologyPage(message, small):
    return render_template("apology.html", message=message, small=small)


def CheckInput(inputText):
    alph = 0
    num = 0
    for i in inputText:
        if i.isalpha():
            alph = alph +1
        if i.isnumeric():
            num = num +1
    if alph > 0 and num > 0:
        return True
    else:
        return False


def CheckLen(inputText, minimum, maximum):
    inputLEN = len(str(inputText))
    if inputLEN >= minimum and inputLEN <= maximum:
        return True
    else:
        return False


def NewUser(InputText):
    connection.execute("SELECT COALESCE ((SELECT username from users where username = %s))", (InputText,))
    rows = connection.fetchone()
    row = rows[0]
    if not row:
        return True
    else:
        return False


def CheckMail(maddress):
    try:
        v = validate_email(maddress)
        if v != EmailNotValidError:
            connection.execute("SELECT COALESCE ((SELECT email from users where email = %s))", (maddress,))
            row = connection.fetchone()
            mail = row[0]
            if not mail:
                # this email is valid and does not exist in db
                return 1 
            else:
                # email is valid, but already existed
                return -1
    except EmailNotValidError:
        # email not valid
        return 0 


def ToStar(mailLocal):
    if len(str(mailLocal)) <= 3:
        return str("*"*len(str(mailLocal)))
    else:
        starLocal = []
        for i in range(0, 2):
            starLocal.append(mailLocal[i])
        for i in range(2, len(str(mailLocal))-1):
            starLocal.append("*")
        starLocal.append(mailLocal[-1])
        starStr = "".join(starLocal)
    return starStr


def CheckLeapYear(YYYY):
    if YYYY%4 == 0:
        if YYYY%100 == 0 and YYYY%400 != 0:
            # not leap
            return False
        else:
            # leap
            return True
    else:
        # leap
        return False


def Jump30(YYYY, MM, DD, hh, mm):
    if mm + 30 >=60:
        mm -= 30
        hh += 1
        if hh == 24:
            hh == 0
            DD += 1
            if DD > 31 and (MM == 1 or MM == 3 or MM == 5 or MM == 7 or MM == 8 or MM == 10):
                MM += 1
                return {"YYYY":YYYY, "MM":MM, "DD":1, "hh":hh, "mm":mm}
            elif DD > 31 and MM == 12:
                YYYY += 1
                return {"YYYY":YYYY, "MM":1, "DD":1, "hh":hh, "mm":mm}
            elif DD > 30 and (MM == 4 or MM == 6 or MM == 9 or MM == 11):
                MM += 1
                return {"YYYY":YYYY, "MM":MM, "DD":1, "hh":hh, "mm":mm}
            elif DD >= 28 and MM == 2 and CheckLeapYear(YYYY) == False:
                return {"YYYY":YYYY, "MM":3, "DD":1, "hh":hh, "mm":mm}
            elif DD >= 28 and MM == 2 and CheckLeapYear(YYYY) == True:
                return {"YYYY":YYYY, "MM":2, "DD":29, "hh":hh, "mm":mm}
            elif DD >= 29 and MM == 2 and CheckLeapYear(YYYY) == True:
                return {"YYYY":YYYY, "MM":3, "DD":1, "hh":hh, "mm":mm}
        else:
            return {"YYYY":YYYY, "MM":MM, "DD":DD, "hh":hh, "mm":mm}
    else:
        return {"YYYY":YYYY, "MM":MM, "DD":DD, "hh":hh, "mm":mm+30}


def LoginRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def GetGroupName(userID):
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    rows = connection.fetchall()
    row = rows[0]
    groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
    jsonG = json.dumps(groupName)
    return jsonG