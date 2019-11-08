from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_mail import Mail, Message
from datetime import date, datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import BadSignature, SignatureExpired, URLSafeSerializer, URLSafeTimedSerializer
from email_validator import EmailNotValidError, validate_email
from helpers import conn, connection, ApologyPage, CheckMail, CheckInput, CheckLen, LoginRequired, NewUser, ToStar

import json
import psycopg2

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_DEFAULT_SENDER"] = ("custom-made-unit Official", "custom.made.unit@gmail.com")
app.config["MAIL_MAX_EMAILS"] = 10
app.config["MAIL_USERNAME"] = "custom.made.unit@gmail.com"
app.config["MAIL_PASSWORD"] = "rinyukarine"
mail = Mail(app)


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")
    maddress = request.form.get("email")

    if not username or not password or not confirmation or not maddress:
        error = ["註冊資訊有短缺，請填完全部欄位。"]
        return render_template("welcome.html", error=error)
    elif CheckInput(username) is False or CheckLen(username, 8, 16) is False:
        error = ["帳號不符合規範，","8-24個字元，至少包含1英文字母、1數字。"]
        return render_template("welcome.html", error=error)
    elif NewUser(username) is False:
        error = ["這個帳號已經被註冊過了，請換一個。"]
        return render_template("welcome.html", error=error)
    elif CheckMail(maddress) == 0:
        error = ["輸入的email無效，","請檢查email拼字、或是換一個email。"]
        return render_template("welcome.html", error=error)
    elif CheckMail(maddress) == -1:
        error = ["這個email已經被使用過了，","請換一個email。"]
        return render_template("welcome.html", error=error)
    elif CheckInput(password) is False or CheckLen(password, 8, 24) is False:
        error = ["密碼不符合規範，","8-24個字元，至少包含1英文字母、1數字。"]
        return render_template("welcome.html", error=error)
    elif password != confirmation:
        error = ["兩次輸入的密碼內容不同，","請檢查。"]
        return render_template("welcome.html", error=error)
    
    hashpass = generate_password_hash(password)
    connection.execute("INSERT INTO users (id,username,hash,email) VALUES (DEFAULT,%s,%s,%s)", 
                        (username, hashpass, maddress))
    conn.commit()
    
    connection.execute("SELECT id,verified FROM users WHERE username = %s", (username,))
    row = connection.fetchone()
    session["id"] = row[0]
    session["verified"] = row[1]
    
    # insert target info (default all NULL) for this userid
    connection.execute("INSERT INTO targets (id,userid) VALUES (DEFAULT,%s)", (row[0],))
    conn.commit()

    # send authenticate email
    connection.execute("SELECT username,email FROM users WHERE id = %s", (row[0],))
    row = connection.fetchone()
    username = row[0]
    email = row[1]

    key = URLSafeTimedSerializer("user-authenticate-key")
    token = key.dumps(email)
    url = "http://127.0.0.1:5000/authenticate/" + token

    # token expired time
    expiredTime = str(datetime.now().replace(microsecond=0) + timedelta(minutes = 30))

    # email contents:
    subject = "[你與○○的距離||custom-made-unit] 新帳號認證"
    message = username + "你好，<br><br>請點選右側連結來啟動帳號：" + url + "<br>謝謝(`・ω・´)<br><br>提示：這個連結會在"\
            + expiredTime \
            + "後過期<br>如果這封信被打開時，連結已經超過賞味期限，請<a href='http://127.0.0.1:5000/gen_token'>點此</a>來取得新的認證email"
    msg = Message(
        subject = subject,
        recipients = [email],
        html = message
    )
    mail.send(msg)

    return redirect(url_for("index"))


@app.route("/newUser")
def newuser(): #for login.html
    username = request.args.get("username")
    if NewUser(username) is True:
        return jsonify(True)
    else:
        return jsonify(False)


@app.route("/mailValidate")
def mailvalid():
    maddress = request.args.get("maddress")
    if CheckMail(maddress) == 1:
        return jsonify(True)
    elif CheckMail(maddress) == -1:
        return jsonify("mailExist")
    else:
        return jsonify("mailFail")


@app.route("/checkUser")
def checkuser(): #for register.html
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
def checkpass(): #for register.html
    pass1 = request.get_json()["pass1"]
    
    if CheckInput(pass1) is False:
        return jsonify("nameContFail")
    if CheckLen(pass1, 8, 24) is False:
        return jsonify("lenFail")
    else:
        return jsonify(True)


@app.route("/gen_token")
@LoginRequired
def token():
    now = datetime.now().replace(microsecond=0)
    last = session.get("last")

    if last is None or (now-last).total_seconds() > 300:
        userID = session.get("id")
        connection.execute("SELECT username,email FROM users WHERE id = %s", (userID,))
        row = connection.fetchone()

        key = URLSafeTimedSerializer("user-authenticate-key")
        token = key.dumps(row[1])
        url = "http://127.0.0.1:5000/authenticate/" + token

        # token expired time
        expiredTime = str(datetime.now().replace(microsecond=0) + timedelta(minutes = 30))

        # email contents:
        subject = "[你與○○的距離||custom-made-unit] 新帳號認證"
        message = row[0] + "你好，<br><br>請點選右側連結來啟動帳號：" + url + "<br>謝謝(`・ω・´)<br><br>提示：這個連結會在"\
            + expiredTime \
            + "後過期<br>如果這封信被打開時，連結已經超過賞味期限，請<a href='http://127.0.0.1:5000/gen_token'>點此</a>來取得新的認證email"

        msg = Message(
            subject = subject,
            recipients = [row[1]],
            html = message
        )
        mail.send(msg)
        session["last"] = now + timedelta(minutes = 5)
        return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))


@app.route("/authenticate/<token>")
def checktoken(token):
    key = URLSafeTimedSerializer("user-authenticate-key")
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
        connection.execute("UPDATE users SET verified = true WHERE email = %s", (plaintext,))
        conn.commit()
        return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    session.clear()
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        error = ["登入資訊有短缺，請輸入帳號與密碼。"]
        return render_template("welcome.html", error=error)
    elif NewUser(username) is True:
        error = ["查無此帳號，請先註冊。"]
        return render_template("welcome.html", error=error)
    
    connection.execute("SELECT hash FROM users WHERE username = (%s)", (username,))
    row = connection.fetchone()
    dbPass = row[0]
    
    if check_password_hash(dbPass, password) is False:
        error = ["密碼不正確，", "<a href='/reset' class='alert-link'>重設密碼？</a>"]
        return render_template("welcome.html", error=error)
    else:
        connection.execute("SELECT id,verified from users WHERE username = %s", (username,))
        row = connection.fetchone()
        # pack user information into session
        session["id"] = row[0]
        session["verified"] = row[1]
        return redirect(url_for("index"))


@app.route("/forget", methods=["POST"])
def forget():
    username = request.form.get("username")
    
    if not username:
        error = ["請輸入帳號。"]
        return render_template("welcome.html", error=error)
    elif NewUser(username) is True:
        error = ["此帳號還未註冊，無法重新設定密碼。"]
        return render_template("welcome.html", error=error)
    else:
        connection.execute("SELECT username,email FROM users WHERE username = %s", (username,))
        row = connection.fetchone()

        key = URLSafeSerializer("user-authenticate-key")
        token = key.dumps(row[0])
        url = "http://127.0.0.1:5000/reset/" + token

        subject = "[你與○○的距離||custom-made-unit] 密碼重置"
        message = row[0] + "你好，<br><br>請點選右側連結來重新設定密碼：" + url + "<br>謝謝(´・ω・`)<br><br>"\
            + "如果沒有重設密碼的需求，請忽略這封信，謝謝。"
        
        msg = Message(
            subject = subject,
            recipients = [row[1]],
            html = message
        )
        mail.send(msg)

        email = validate_email(row[1])
        starMail = str(ToStar(str(email["local"])) + "@" + str(email["domain"]))
        error = ["重置密碼的信已經發到"+starMail+"，請依照信中說明來重新設定密碼，謝謝。"]
        return render_template("welcome.html", error=error)


@app.route("/reset/<token>")
def reset(token):
    key = URLSafeSerializer("user-authenticate-key")
    try:
        plaintext = key.loads(token)
        session["reset"] = plaintext
        return redirect(url_for("password"))
    except BadSignature:
        return redirect(url_for("password"))


@app.route("/reset", methods=["GET", "POST"])
def password():
    if request.method == "POST":
        username = session.get("reset")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            session.clear()
            return render_template("password.html")
        elif not password or not confirmation:
            session["error"] = "請輸入密碼與確認密碼"
            return render_template("password.html")
        elif CheckInput(password) is False or CheckLen(password, 8, 24) is False:
            session["error"] = "密碼不符合規範，長度為8-24個字元，至少包含1英文字母、1數字。"
            return render_template("password.html")
        elif password != confirmation:
            session["error"] = "兩次輸入的密碼內容不同，請檢查。"
            return render_template("password.html")
        else:
            hashpass = generate_password_hash(password)
            connection.execute("UPDATE users SET hash = %s WHERE username = %s", (hashpass,username))
            conn.commit()
            session.clear()
            error = ["密碼重設成功，請使用新密碼登入，謝謝。"]
            return render_template("welcome.html", error=error)
    else:
        return render_template("password.html") # here "GET" is recirect from reset()


@app.route("/confStatus", methods=["POST"])
@LoginRequired
def verify(): # for nav-bar
    userID = session.get("id")
    connection.execute("SELECT COALESCE ((SELECT verified from users where id = %s))", (userID,))
    row = connection.fetchone()   

    if row[0] is None:
        return jsonify(False)
    else:
        # the account is confirmed
        return jsonify(True)
    

@app.route("/")
@LoginRequired
def index():
    userID = session.get("id")
    verified = session.get("verified")

    if not verified:
        connection.execute("SELECT username,email FROM users WHERE id = %s", (userID,))
        row = connection.fetchone()
        email = validate_email(row[1])
        starMail = str(ToStar(str(email["local"])) + "@" + str(email["domain"]))
        return render_template("index.html", username=row[0], email=starMail)
    else:
        # get this month's bill(s) SUM
        NOW = datetime.now()
        dateStart = int(str(NOW.year)+str(NOW.month)+str(0)+str(0))
        dateEnd = int(str(NOW.year)+str(NOW.month)+str(32))
        connection.execute("SELECT SUM(amount) FROM bills WHERE userid = %s AND datestamp BETWEEN %s AND %s", \
                            (userID,dateStart,dateEnd))
        row = connection.fetchone()
        
        # in case of no bill
        if row[0] is None:
            amount = 0
        else:
            amount = row[0]
        
        # get target-setting status
        connection.execute("SELECT targetunit,target,targetamount from targets where userid = %s", (userID,))
        row = connection.fetchone()
        
        # no targetamount info
        if row[2] is None:
            session["targetamount"] = None
            return render_template("index.html", amount=amount, YYYY=str(NOW.year), MM=str(NOW.month))
        else:
            session["targetamount"] = True
            targets = [row[i] for i in range(0,2) if row[i] is not None] # only display not null target(s)
            percentage = round(float(amount)/float(row[2]),2)
            return render_template("index.html", amount=amount, targets=targets, percentage=percentage)
            # amount為0的時候(當月沒有記帳紀錄) ==> 顯示「本月沒有記帳紀錄」


@app.route("/queryMonthSum", methods=["POST"])
@LoginRequired
def monthsum(): # for index.html
    userID = session.get("id")
    dateStart = int("".join(request.get_json()["date"].split("-"))+str(0)+str(0))
    dateEnd = int("".join(request.get_json()["date"].split("-"))+str(32))
    connection.execute("SELECT SUM(amount) FROM bills WHERE userid = %s AND datestamp BETWEEN %s AND %s", \
                        (userID,dateStart,dateEnd))
    row = connection.fetchone()
    
    if row[0] is None: # no bill record
        result = {"amount": 0, "percentage": 0}
        return jsonify(result)
    else:
        connection.execute("SELECT targetamount FROM targets WHERE userid = %s", (userID,))
        target = connection.fetchone()
        result = {"amount": row[0], "percentage": (row[0]/target[0])}
        return jsonify(result)


@app.route("/add", methods=["GET", "POST"])
@LoginRequired
def add():
    userID = session.get("id")
    if request.method == "POST":
        groupKey = request.form.get("group")
        amount = request.form.get("amount")
        notes = request.form.get("notes")        
        dateStamp = request.form.get("dateStamp")

        if not groupKey or not amount or not dateStamp:
            return ApologyPage("記帳資料有缺","是否有漏填欄位？")
        
        try:
            # YYYY-MM-DD ==> YYYYMMDD
            dateStamp = int("".join((request.form.get("dateStamp")).split("-")))
        except AttributeError:
            return ApologyPage("日期格式有誤","提示：請透過網頁日曆中選取日期")

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
        return redirect(url_for("index"))
    else:
        connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
        row = connection.fetchone()
        groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}
        return render_template("add.html", groupName=groupName)


@app.route("/view")
@LoginRequired
def view():
    userID = session.get("id")
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    row = connection.fetchone()
    groupName = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]} # for bill edit usage

    return render_template("view.html", groupName=groupName.items())
    
    
@app.route("/filter", methods=["POST"])
@LoginRequired
def filter(): # for view.html
    userID = session.get("id")
    start =  int("".join((request.get_json()["start"]).split("-")))
    end = int("".join((request.get_json()["end"]).split("-")))

    connection.execute("SELECT id,datestamp,groupkey,notes,amount FROM bills \
                        WHERE (datestamp BETWEEN %s AND %s) AND userid = %s ORDER BY datestamp", (start,end,userID))
    rows = connection.fetchall()

    connection.execute("SELECT g0,g1,g2,g3 FROM users WHERE id = %s",(userID,))
    groupRow = connection.fetchone()
    groupName = {"g0":groupRow[0], "g1":groupRow[1], "g2":groupRow[2], "g3":groupRow[3]}

    if not rows:
        return jsonify(False)
    else:
        bills = []
        for items in rows:
            tr = []
            for i in items:
                if i in groupName:
                    tr.append(groupName[i]) # append group name according to groupKey
                else:
                    tr.append(i)
            bills.append(tr)
        return jsonify(bills)


@app.route("/billEdit", methods=["POST"])
@LoginRequired
def edit():
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
def delete():
    toDelete = request.get_json()["id"]
    connection.execute("DELETE from bills WHERE id = %s", (toDelete,))
    conn.commit()
    return jsonify(True)


@app.route("/setting") # nav-bar right-side
@LoginRequired
def setting():
    userID = session.get("id")

    #pull target status from db
    connection.execute("SELECT target,targetamount,targetunit from targets where userid = %s", (userID,))
    row = connection.fetchone()

    target = row[0]
    targetAmount = row[1]
    targetUnit = row[2]
    
    #pull group names from db
    connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
    row = connection.fetchone()
    groupName = [row[0], row[1], row[2], row[3]]

    return render_template("setting.html", groupName=groupName, target=target, targetAmount=targetAmount, targetUnit=targetUnit)
    
    #修改email


@app.route("/updateTarget", methods=["POST"])
@LoginRequired
def updatetargets():
    userID = session.get("id")
    tType = request.get_json()["tType"]
    tContent = request.get_json()["content"]
    
    if tType == "targetAmount":
        connection.execute("UPDATE targets SET targetamount = %s WHERE userid = %s", (tContent,userID))
        conn.commit()
        connection.execute("SELECT targetamount FROM targets WHERE userid = %s", (userID,))
    if tType == "target":
        connection.execute("UPDATE targets SET target = %s WHERE userid = %s", (tContent,userID))
        conn.commit()
        connection.execute("SELECT target FROM targets WHERE userid = %s", (userID,))
    if tType == "targetUnit":
        connection.execute("UPDATE targets SET targetunit = %s WHERE userid = %s", (tContent,userID))
        conn.commit()
        connection.execute("SELECT targetunit FROM targets WHERE userid = %s", (userID,))
    
    row = connection.fetchone()
    return jsonify(row[0])


@app.route("/updateGroupName", methods=["POST"])
@LoginRequired
def updategroup():
    userID = session.get("id")
    gNames = request.get_json()["gNames"]
    updateName = request.get_json()["updateName"]

    if not gNames or not updateName or len(str(updateName)) > 24:
        return jsonify(False)
    else:
        connection.execute(f"UPDATE users SET {gNames} = %s WHERE id = %s", (updateName,userID))
        conn.commit()
        # get updated group name(s)
        connection.execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userID,))
        groupName = connection.fetchone()
        return jsonify(groupName)


@app.route("/updatePass", methods=["POST"])
@LoginRequired
def updatepass():
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


@app.route("/welcome")
def welcome():
    return render_template("welcome.html", error=None)