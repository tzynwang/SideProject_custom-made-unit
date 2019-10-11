import json
import os
import psycopg2
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


conn = psycopg2.connect(database="d4si1co4s3p2gi", 
                        user="mjyufuhmpotxwl", 
                        password="308d87d49fb8710befb9df22342570abaf26a0b16a3ab24fab0a87796f984943", 
                        host="ec2-174-129-218-200.compute-1.amazonaws.com", port="5432")
connection = conn.cursor()


def apologyPage(message, small):
    return render_template("apology.html", message=message, small=small)


def checkInput(inputText):
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


def checkLen(inputText, minimum, maximum):
    inputLEN = len(str(inputText))
    if inputLEN >= minimum and inputLEN <= maximum:
        return True
    else:
        return False


def loginRequired(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def newUser(InputText):
    connection.execute("SELECT COALESCE ((SELECT username from users where username = %s))", (InputText,))
    rows = connection.fetchone()
    row = rows[0]
    if not row:
        return True
    else:
        return False


def getGroupName(userID):
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    rows = connection.fetchall()
    row = rows[0]
    groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
    jsonG = json.dumps(groupName)
    return jsonG