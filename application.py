from collections import defaultdict
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import conn, connection, LoginRequired, CheckInput, CheckLen, NewUser, ApologyPage, CheckMail, ToStar, Jump30
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from email_validator import validate_email, EmailNotValidError

import psycopg2
import json

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = ('custom-made-unit Official', 'custom.made.unit@gmail.com')
app.config['MAIL_MAX_EMAILS'] = 10
app.config['MAIL_USERNAME'] = 'custom.made.unit@gmail.com'
app.config['MAIL_PASSWORD'] = 'unitmadecustoms'
mail = Mail(app)

def sendAuthMail(ID):
    userID = ID
    connection.execute("SELECT username, email FROM users WHERE id = %s", (userID,))
    row = connection.fetchone()
    username = row[0]
    email = row[1]

    key = URLSafeTimedSerializer('user-authenticate-key')
    token = key.dumps(email)
    URL = "http://127.0.0.1:5000/authenticate/" + token

    # token expired time
    NOW = datetime.now()
    expiredTime = Jump30(NOW.year, NOW.month, NOW.day, NOW.hour, NOW.minute)
    exY = expiredTime["YYYY"]
    exMon = expiredTime["MM"]
    exD = expiredTime["DD"]
    exh = expiredTime["hh"]
    exmin = expiredTime["mm"]

    # email contents:
    subject = '[你與○○的距離||custom-made-unit] 新帳號認證'
    message = username + '你好，<br><br>請點選右側連結來啟動帳號：' + URL + '<br>謝謝(`・ω・´)<br><br>提示：這個連結會在'\
            + str(exY) + '/' + str(exMon) + '/' + str(exD) + ' ' + str(exh) + ':' + str(exmin) \
            + '後過期<br>如果這封信被打開時，連結已經超過賞味期限，請<a href="http://127.0.0.1:5000/gen_token">點此</a>來取得新的認證email'
    msg = Message(
        subject = subject,
        recipients = [email],
        html = message
    )
    mail.send(msg)
    return True


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        maddress = request.form.get("email")

        if not username or not password or not confirmation or not maddress:
            return ApologyPage("缺少註冊必要資訊","表格全部填寫了嗎？")
        elif CheckInput(username) is False:
            return ApologyPage("帳號組成內容不符合規範","8-16個字元，至少包含1英文字母、1數字")
        elif CheckLen(username, 8, 16) is False:
            return ApologyPage("帳號長度不符合規則","8-16個字元，至少包含1英文字母、1數字")
        elif NewUser(username) is False:
            return ApologyPage("這個帳號已經被註冊過了","請換一個")
        elif CheckMail(maddress) == 0:
            return ApologyPage("輸入的email無效","請檢查email拼字、或是換一個email")
        elif CheckMail(maddress) == -1:
            return ApologyPage("這個email已經被使用過了","請換一個email")
        elif CheckInput(password) is False:
            return ApologyPage("密碼組成內容不符合規範","8-24個字元，至少包含1英文字母、1數字")
        elif CheckLen(password, 8, 24) is False:
            return ApologyPage("密碼長度不符合規則","8-24個字元，至少包含1英文字母、1數字")
        elif password != confirmation:
            return ApologyPage("兩次輸入的密碼內容不同","請檢查")
        else:
            hashpass = generate_password_hash(password)
            connection.execute("INSERT INTO users (id,username,hash,email) VALUES (DEFAULT,%s,%s,%s)", 
                                (username, hashpass, maddress))
            conn.commit()
            # pack user information into session
            connection.execute("SELECT id FROM users WHERE username = %s", (username,))
            row = connection.fetchone()
            session["id"] = row[0]
            # send authenticate email
            if sendAuthMail(row[0]) == True:
                return redirect(url_for('index'))
    else:
        return render_template("register.html")


@app.route("/newUser")
def isNew():
    """for login.html"""
    username = request.args.get("username")
    if NewUser(username) is True:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route("/mailValidate")
def validMail():
    maddress = request.args.get("maddress")
    if CheckMail(maddress) == 1:
        return jsonify(True)
    elif CheckMail(maddress) == -1:
        return jsonify("mailExist")
    else:
        return jsonify("mailFail")


@app.route("/checkUser")
def checkUser():
    """for register.html"""
    username = request.args.get("username")
    
    if NewUser(username) is False:
        return jsonify("userExist")
    if CheckInput(username) is False:
        return jsonify("nameContFail")
    if CheckLen(username, 8, 16) is False:
        return jsonify("lenFail")
    else:
        return jsonify(True)


@app.route("/checkPass", methods=["POST"])
def checkPass():
    """for register.html"""
    pass1 = request.get_json()["pass1"]
    
    if CheckInput(pass1) is False:
        return jsonify("nameContFail")
    if CheckLen(pass1, 8, 24) is False:
        return jsonify("lenFail")
    else:
        return jsonify(True)


@app.route("/gen_token")
def send_authenticate():
    userID = session.get("id")
    connection.execute("SELECT username,email,conf FROM users WHERE id = %s", (userID,))
    row = connection.fetchone()
    username = row[0]
    email = row[1]
    confStatus = row[2]

    if confStatus != True:
        key = URLSafeTimedSerializer('user-authenticate-key')
        token = key.dumps(email)
        URL = "http://127.0.0.1:5000/authenticate/" + token

        # token expired time
        NOW = datetime.now()
        expiredTime = Jump30(NOW.year, NOW.month, NOW.day, NOW.hour, NOW.minute)
        exY = expiredTime["YYYY"]
        exMon = expiredTime["MM"]
        exD = expiredTime["DD"]
        exh = expiredTime["hh"]
        exmin = expiredTime["mm"]

        # email contents:
        subject = '[你與○○的距離||custom-made-unit] 新帳號認證'
        message = username + '你好，<br><br>請點選右側連結來啟動帳號：' + URL + '<br>謝謝(`・ω・´)<br><br>提示：這個連結會在'\
            + str(exY) + '/' + str(exMon) + '/' + str(exD) + ' ' + str(exh) + ':' + str(exmin) \
            + '後過期<br>如果這封信被打開時，連結已經超過賞味期限，請<a href="http://127.0.0.1:5000/gen_token">點此</a>來取得新的認證email'

        msg = Message(
            subject = subject,
            recipients = [email],
            html = message
        )
        mail.send(msg)

        v = validate_email(email)
        mailLocal = str(v["local"])
        domain = str(v["domain"])
        starStr = ToStar(mailLocal)
        starMail = str(starStr + "@" + domain)

        return render_template("index.html", confStatus=0, username=username, email=starMail)
    else:
        return render_template("index.html")


@app.route("/authenticate/<token>")
def check_authenticate(token):
    key = URLSafeTimedSerializer('user-authenticate-key')
    try:
        plaintext = key.loads(token, max_age=1800)
    except SignatureExpired:
        return render_template("auth_0.html", status="token過期")
    except BadSignature:
        return render_template("auth_0.html", status="token無效")
    
    # check if plaintext(email) exists in db
    connection.execute("SELECT COALESCE ((SELECT email from users where email = %s))", (plaintext,))
    rows = connection.fetchone()
    row = rows[0]
    
    if not row:
        return ApologyPage("user not exits", "this email doesn't exist in our database.")
    else:
        connection.execute("UPDATE users SET conf = true WHERE email = %s", (plaintext,))
        conn.commit()
        return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if not username or not password:
            return ApologyPage("登入資訊不完整","請輸入帳號與密碼")
            
        if NewUser(username) is True:
            return ApologyPage("查無此帳號","請先註冊")
        
        connection.execute("SELECT hash FROM users WHERE username = (%s)", (username,))
        row = connection.fetchone()
        dbPass = row[0]
        
        if check_password_hash(dbPass, password) is False:
            return ApologyPage("密碼不正確","請檢查")
        else:
            connection.execute("SELECT id from users WHERE username = %s", (username,))
            row = connection.fetchone()
            # pack user information into session
            session["id"] = row[0]
            return redirect(url_for('index'))
    else:
        return render_template("login.html")


@app.route("/")
@LoginRequired
def index():
    userID = session.get("id")
    # account confirmation status check
    connection.execute("SELECT conf,username,email FROM users WHERE id = %s", (userID,))
    row = connection.fetchone()
    confStatus = row[0]
    username = row[1]
    email = row[2]
    
    # email not yet confirm
    if confStatus != True: 
        v = validate_email(email)
        mailLocal = str(v["local"])
        domain = str(v["domain"])
        starStr = ToStar(mailLocal)
        starMail = str(starStr + "@" + domain)
        return render_template("index.html", confStatus=0, username=username, email=starMail)
    else:
        # get accounting amount info
        NOW = datetime.now()
        dateStart = int(str(NOW.year)+str(NOW.month)+str(0)+str(0))
        dateEnd = int(str(NOW.year)+str(NOW.month)+str(32))
        connection.execute("SELECT SUM(amount) FROM bills WHERE userid = %s AND datestamp BETWEEN %s AND %s", (userID,dateStart,dateEnd))
        row = connection.fetchone()
        
        # in case of no bill
        if row[0] is None:
            amount = 0
        else:
            amount = row[0]
        
        # get target-setting status
        connection.execute("SELECT targetunit,target,targetamount from targets where userid = %s", (userID,))
        row = connection.fetchone()
        
        # no target/targetamount/targetunit info
        if not row: 
            return render_template("index.html", targetStatus=0, amount=amount, YYYY=str(NOW.year), MM=str(NOW.month))
        else:
            t = [row[i] for i in range(0,2) if row[i] is not None] # only display not null target info at front end
            percentage = round(float(amount)/float(row[2]),2) # row[2]: targetamount
            return render_template("index.html", targetStatus=1, amount=amount, YYYY=str(NOW.year), MM=str(NOW.month), t=t, percentage=percentage)


@app.route("/add", methods=["GET", "POST"])
@LoginRequired
def add():
    userID = session.get("id")
    if request.method == "POST":
        groupKey = request.form.get("group")
        amount = request.form.get("amount")
        notes = request.form.get("notes")        
        dateStamp = int("".join((request.form.get("dateStamp")).split("-"))) # YYYY-MM-DD ==> YYYYMMDD

        if not groupKey or not amount or not dateStamp:
            return ApologyPage("記帳資料有缺","是否有漏填欄位？")
        
        try:
            amountInt = int(amount)
        except ValueError:
            return ApologyPage("記帳金額格式有誤","提示：只能輸入正整數")
        
        if amountInt < 1:
            return ApologyPage("記帳金額有誤","提示：最低記帳金額為1元")

        connection.execute("INSERT INTO bills (id,userid,groupkey,amount,notes,datestamp) \
                            VALUES (DEFAULT,%s,%s,%s,%s,%s)",
                            (userID,groupKey,amountInt,notes,dateStamp))
        conn.commit()
        return redirect(url_for('index'))
    else:
        connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
        rows = connection.fetchall()
        row = rows[0]
        groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
        return render_template("add.html", groupName=groupName)


@app.route("/view")
@LoginRequired
def view():
    #display bill(s)
    userID = session.get("id")
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    rows = connection.fetchall()
    row = rows[0]
    groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]} # for bill edit usage

    return render_template("view.html", groupName=groupName.items())
    
    
@app.route("/filter", methods=["POST"])
@LoginRequired
def Filter():
    
    userID = session.get("id")
    
    start =  int("".join((request.get_json()["start"]).split("-")))
    end = int("".join((request.get_json()["end"]).split("-")))

    connection.execute("SELECT id,datestamp,groupkey,notes,amount FROM bills \
                        WHERE (datestamp BETWEEN %s AND %s) AND userid = %s ORDER BY datestamp", (start,end,userID))
    rows = connection.fetchall()

    connection.execute("SELECT g0,g1,g2,g3 FROM users WHERE id = %s",(userID,))
    names = connection.fetchone()
    nameRef = {"g0":names[0], "g1":names[1], "g2":names[2], "g3":names[3]}

    if not rows:
        return jsonify(False)
    else:
        bills = []
        for items in rows:
            tr = []
            for i in items:
                if i in nameRef:
                    tr.append(nameRef[i])
                else:
                    tr.append(i)
            bills.append(tr)
        return jsonify(bills)


@app.route("/billEdit", methods=["POST"])
@LoginRequired
def Edit():
    toUpdate = request.get_json()["content"]
    ID = toUpdate["id"]
    
    for k,v in toUpdate.items():
        if k == "ediDate":
            newDate = int(v)
            connection.execute("UPDATE bills SET datestamp = %s WHERE id = %s",(newDate,ID))
            conn.commit()
        if k == "ediGroup":
            connection.execute("UPDATE bills SET groupkey = %s WHERE id = %s",(v,ID))
            conn.commit()
        if k == "ediNote":
            connection.execute("UPDATE bills SET notes = %s WHERE id = %s",(v,ID))
            conn.commit()
        if k == "ediAmount":
            connection.execute("UPDATE bills SET amount = %s WHERE id = %s",(v,ID))
            conn.commit()
    return jsonify(True)


@app.route("/billDelete", methods=["POST"])
@LoginRequired
def Delete():
    toDelete = request.get_json()["id"]
    connection.execute("DELETE from bills WHERE id = %s", (toDelete,))
    return jsonify(True)


@app.route("/groupToName")
@LoginRequired
def ToName():
    userID = session.get("id")
    groupNo = str(request.args.get("groupNo"))
    
    connection.execute(f"SELECT {groupNo} FROM users WHERE id = {userID}")
    row = connection.fetchone()
    groupName = str(row[0])
    return jsonify(groupName)


@app.route("/setting") #右側
@LoginRequired
def Setting():
    userID = session.get("id")

    """pull target status from db"""
    connection.execute("SELECT COALESCE ((SELECT target from targets where userid = %s))", (userID,))
    rows = connection.fetchone()
    row = rows[0]
    if not row: 
        targetStatus = 0
        targetAmount = 0
    else:
        connection.execute("SELECT target,targetamount from targets where userid = %s", (userID,))
        rows = connection.fetchone()
        targetStatus = rows[0]
        targetAmount = rows[1]
    
    """pull group names from db"""
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    rows = connection.fetchall()
    row = rows[0]
    groupName = [row[0], row[1], row[2], row[3]]

    return render_template("setting.html", groupName=groupName, targetStatus=targetStatus, targetAmount=targetAmount)
    
    #修改email


@app.route("/setTarget", methods=["POST"])
@LoginRequired
def SetTarget():
    userID = session.get("id")
    
    targetName = str(request.get_json()["targetName"])
    targetAmount = request.get_json()["targetAmount"]

    if len(targetName) > 24:
        return jsonify("NameTooLong")
    try:
        amountInt = int(targetAmount)
    except ValueError:
        return jsonify("NotInt")
    if amountInt < 1:
        return jsonify("AmountNotValid")
    
    connection.execute("INSERT INTO targets (id,userid,target,targetamount) VALUES (DEFAULT,%s,%s,%s)", (userID,targetName,amountInt))
    conn.commit()
    return jsonify(True)


@app.route("/updateTargetName", methods=["POST"])
@LoginRequired
def UpdateTargetName():
    userID = session.get("id")
    targetName = str(request.get_json()["targetName"])

    if len(targetName) > 0 and len(targetName) <= 24:
        connection.execute("UPDATE targets SET target = %s WHERE userid = %s", (targetName,userID))
        conn.commit()
        return jsonify(True)
    else:
        pass


@app.route("/getNewTargetName")
@LoginRequired
def NewTargetName():
    userID = session.get("id")
    connection.execute("SELECT target FROM targets WHERE userid = %s", (userID,))
    row = connection.fetchone()
    return jsonify(row[0])


@app.route("/getNewTargetAmount")
@LoginRequired
def NewTargetAmount():
    userID = session.get("id")
    connection.execute("SELECT targetamount FROM targets WHERE userid = %s", (userID,))
    row = connection.fetchone()
    return jsonify(row[0])


@app.route("/updateTargetAmount", methods=["POST"])
@LoginRequired
def UpdateTargetAmount():
    userID = session.get("id")
    targetAmount = int(request.get_json()["targetAmount"])
    connection.execute("UPDATE targets SET targetamount = %s WHERE userid = %s", (targetAmount,userID))
    conn.commit()
    return jsonify(True)


@app.route("/getGroupName")
@LoginRequired
def GetGroupName():
    userID = session.get("id")
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    rows = connection.fetchall()
    row = rows[0]
    groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
    jsonG = json.dumps(groupName)
    return jsonG


@app.route("/updateGroupName", methods=["POST"])
@LoginRequired
def UpdateGroupName():
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
@LoginRequired
def UpdatePass():
    userID = session.get("id")
    newPass = request.get_json()["pass1"]
    newHash = generate_password_hash(newPass)
    
    connection.execute("UPDATE users SET hash = %s WHERE id = %s",(newHash, userID))
    conn.commit()
    return jsonify(True)


@app.route("/logout")
@LoginRequired
def logout():
    session.clear()
    return redirect("/")