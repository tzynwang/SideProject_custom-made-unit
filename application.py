from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import conn, connection, loginRequired, checkInput, checkLen, newUser, apologyPage

import psycopg2
import json

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        print(username)
        print(password)
        
        if not username or not password or not confirmation:
            return apologyPage("缺少註冊必要資訊","表格全部填寫了嗎？")
        elif checkInput(username) is False:
            return apologyPage("帳號組成內容不符合規範","8-16個字元，至少包含1英文字母、1數字")
        elif checkLen(username, 8, 16) is False:
            return apologyPage("帳號長度不符合規則","8-16個字元，至少包含1英文字母、1數字")
        elif newUser(username) is False:
            return apologyPage("這個帳號已經被註冊過了","請換一個")
        elif checkInput(password) is False:
            return apologyPage("密碼組成內容不符合規範","8-24個字元，至少包含1英文字母、1數字")
        elif checkLen(password, 8, 24) is False:
            return apologyPage("密碼長度不符合規則","8-24個字元，至少包含1英文字母、1數字")
        elif password != confirmation:
            return apologyPage("兩次輸入的密碼內容不同","請檢查")
        else:
            hashpass = generate_password_hash(password)
            connection.execute("INSERT INTO users (id,username,hash) VALUES (DEFAULT,%s,%s)", (username, hashpass))
            conn.commit()
            # pack user information into session
            connection.execute("SELECT id FROM users WHERE username = %s", (username,))
            row = connection.fetchone()
            session["id"] = row[0]
            return redirect(url_for('index'))
    else:
        return render_template("register.html")


@app.route("/newUser")
def isNew():
    """for login.html"""
    username = request.args.get("username")
    if newUser(username) is True:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route("/checkUser")
def checkUser():
    """for register.html"""
    username = request.args.get("username")
    
    if newUser(username) is False:
        return jsonify("userExist")
    if checkInput(username) is False:
        return jsonify("nameContFail")
    if checkLen(username, 8, 16) is False:
        return jsonify("lenFail")
    else:
        return jsonify(True)


@app.route("/checkPass", methods=["POST"])
def checkPass():
    """for register.html"""
    pass1 = request.get_json()["pass1"]
    
    if checkInput(pass1) is False:
        return jsonify("nameContFail")
    if checkLen(pass1, 8, 24) is False:
        return jsonify("lenFail")
    else:
        return jsonify(True)


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            return apologyPage("登入資訊不完整","請輸入帳號與密碼")
            
        if newUser(username) is True:
            return apologyPage("查無此帳號","請先註冊")
        
        connection.execute("SELECT hash FROM users WHERE username = (%s)", (username,))
        row = connection.fetchone()
        dbPass = row[0]
        
        if check_password_hash(dbPass, password) is False:
            return apologyPage("密碼不正確","請檢查")
        else:
            connection.execute("SELECT id from users WHERE username = %s", (username,))
            row = connection.fetchone()
            # pack user information into session
            session["id"] = row[0]
            return redirect(url_for('index'))
    else:
        return render_template("login.html")


@app.route("/")
@loginRequired
def index():
    #讓使用者選擇顯示某區段日期的花費
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
@loginRequired
def add():
    userID = session.get("id")
    if request.method == "POST":
        groupKey = request.form.get("group")
        amount = request.form.get("amount")
        notes = request.form.get("notes")
        YYYY = request.form.get("YYYY")
        MM = request.form.get("MM")
        DD = request.form.get("DD")
        hh = request.form.get("hh")
        mm = request.form.get("mm")

        if not groupKey or not amount or not YYYY or not MM or not DD or not hh or not mm:
            return apologyPage("記帳資料有缺","是否有漏填欄位？")
        
        try:
            amountInt = int(amount)
        except ValueError:
            return apologyPage("記帳金額格式有誤","提示：(目前)只能輸入正整數")
        
        if amountInt < 1:
            return apologyPage("記帳金額有誤","提示：最低記帳金額為1元")

        connection.execute("INSERT INTO bills (id,userid,groupkey,amount,notes,datey,datemo,dated,dateh,datemin) \
                            VALUES (DEFAULT,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                            (userID,groupKey,amountInt,notes,YYYY,MM,DD,hh,mm))
        conn.commit()

        return redirect(url_for('index'))
    else:
        connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
        rows = connection.fetchall()
        row = rows[0]
        groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
        
        NOW = datetime.now()
        YYYY = NOW.year
        MM = NOW.month
        DD = NOW.day
        hh = NOW.hour
        mm = NOW.minute

        return render_template("add.html", groupName=groupName, YYYY=YYYY, MM=MM, DD=DD, hh=hh, mm=mm)


@app.route("/edit", methods=["GET", "POST"])
@loginRequired
def edit():
    #讓使用者選擇日期區段後，點選目標編輯記帳金額、日期與文字備註
    return render_template("edit.html")


@app.route("/setting") #右側
@loginRequired
def setting():
    """pull group names from db"""
    userID = session.get("id")
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    rows = connection.fetchall()
    row = rows[0]
    groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
    jsonG = json.dumps(groupName)
    return render_template("setting.html", jsonG=jsonG)
    
    #修改帳號(email)


@app.route("/getGroupName")
@loginRequired
def getGroupName():
    userID = session.get("id")
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    rows = connection.fetchall()
    row = rows[0]
    groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
    jsonG = json.dumps(groupName)
    return jsonG


@app.route("/updateGroupName", methods=["POST"])
@loginRequired
def updateGroupName():
    userID = session.get("id")
    gNames = request.get_json()["gNames"]
    updateName = request.get_json()["updateName"]

    if not gNames or not updateName or len(str(updateName)) > 24:
        return jsonify(False)
    else:
        connection.execute(f"UPDATE users SET {gNames} = %s WHERE id = %s", (updateName,userID))
        conn.commit()
        return jsonify(True)


@app.route("/updatePass", methods=["POST"])
@loginRequired
def updatePass():
    userID = session.get("id")
    newPass = request.get_json()["pass1"]
    newHash = generate_password_hash(newPass)
    
    connection.execute("UPDATE users SET hash = %s WHERE id = %s",(newHash, userID))
    conn.commit()
    return jsonify(True)


@app.route("/logout")
@loginRequired
def logout():
    session.clear()
    return redirect("/")    