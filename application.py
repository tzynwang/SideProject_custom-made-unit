import os
from datetime import datetime, timedelta

import psycopg2

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import BadSignature, SignatureExpired, URLSafeSerializer, URLSafeTimedSerializer
from email_validator import validate_email
from flask_session import Session
from helpers import db_connection, new_user, verify_input, verify_len, verify_mail, to_star, login_required


app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")
app.config["SESSION_PERMANENT"] = os.environ.get("SESSION_PERMANENT")
app.config["SESSION_PERMANENT_LIFETIME"] = os.environ.get("SESSION_PERMANENT_LIFETIME")
app.config["SESSION_TYPE"] = os.environ.get("SESSION_TYPE")
Session(app)

app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER")
app.config["MAIL_PORT"] = os.environ.get("MAIL_PORT")
app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")
app.config["MAIL_MAX_EMAILS"] = os.environ.get("MAIL_MAX_EMAILS")
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
mail = Mail(app)

app.jinja_env.line_comment_prefix = "##"


@app.route("/welcome")
def welcome():
    """intro page, leads to register/login"""
    return render_template("welcome.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")

        if not username or not password or not confirmation or not email:
            return render_template("register.html", error="註冊資訊有短缺，請填完全部欄位。")
        elif (verify_input(username) or verify_len(username, 8, 16)) is False:
            return render_template("register.html", error="帳號不符合規範：8-16個字元，至少包含1英文字母、1數字。")
        elif new_user(username) is False:
            return render_template("register.html", error="這個帳號已經被註冊過了，請換一個。")
        elif verify_mail(email) == "mail_invalid":
            return render_template("register.html", error="輸入的email無效：請檢查email拼字、或是換一個email。")
        elif verify_mail(email) == "mail_existed":
            return render_template("register.html", error="這個email已經被使用過了，請換一個email。")
        elif (verify_input(password) or verify_len(password, 8, 24)) is False:
            return render_template("register.html", error="密碼不符合規範：8-24個字元，至少包含1英文字母、1數字。")
        elif password != confirmation:
            return render_template("register.html", error="兩次輸入的密碼內容不同，請檢查。")

        conn = db_connection()
        hashpass = generate_password_hash(password)
        conn[0].execute("INSERT INTO users (id,username,hash,email) VALUES (DEFAULT,%s,%s,%s)",
                           (username, hashpass, email))
        conn[1].commit()

        conn[0].execute("SELECT id,verified FROM users WHERE username = %s", (username,))
        row = conn[0].fetchone()
        session["id"] = row[0]
        session["verified"] = row[1]

        # insert target info (default all NULL) for this userid
        conn[0].execute("INSERT INTO targets (id,userid) VALUES (DEFAULT,%s)", (row[0],))
        conn[1].commit()

        # send authenticate email
        conn[0].execute("SELECT username,email FROM users WHERE id = %s", (row[0],))
        row = conn[0].fetchone()
        username = row[0]
        email = row[1]

        key = URLSafeTimedSerializer(os.environ.get("SECRET_KEY"))
        token = key.dumps(email)
        url = os.environ.get("URL") + "/token/verify/" + token
        link = "<a href=" + url + ">點我啟動帳號</a>"

        # token expired time
        expired_time = str(datetime.now().replace(microsecond=0) + timedelta(minutes=30))

        # email contents:
        subject = "[你與○○的距離||custom-made-unit] 新帳號認證"
        message = username + "您好，<br><br>請點選右側連結來啟動帳號："\
                + link + "<br>謝謝(`・ω・´)<br><br>提示：這個連結會在"\
                + expired_time \
                + "後過期<br>如果這封信被打開時，連結已經超過賞味期限，"\
                + "請<a href='" + os.environ.get("URL") + "/token/sent'>點此</a>來取得新的認證email"
        msg = Message(
            subject=subject,
            recipients=[email],
            html=message
        )
        mail.send(msg)
        return redirect(url_for("index"))
    else:
        return render_template("register.html", error=None)


@app.route("/check/mail")
def check_mail():
    """for register/pass_forget.html"""
    email = request.args.get("email")
    if verify_mail(email) == "mail_new":
        return jsonify(True)
    if verify_mail(email) == "mail_existed":
        return jsonify("mailExist")
    else:
        return jsonify("mailFail")


@app.route("/check/user")
def check_user():
    """for login/register/pass_forget.html"""
    username = request.args.get("username")
    if new_user(username) is False:
        return jsonify("userExist")
    elif verify_input(username) is False:
        return jsonify("nameContFail")
    elif verify_len(username, 8, 16) is False:
        return jsonify("lenFail")
    else:
        return jsonify(True)


@app.route("/check/pass", methods=["POST"])
def check_pass():
    """for register/password/setting.html"""
    pass1 = request.get_json()["pass1"]
    if verify_input(pass1) is False:
        return jsonify("nameContFail")
    if verify_len(pass1, 8, 24) is False:
        return jsonify("lenFail")
    return jsonify(True)


@app.route("/token/sent")
@login_required
def token_sent():
    now = datetime.now().replace(microsecond=0)
    last = session.get("last")

    if last is None or (now-last).total_seconds() > 300:
        userid = session.get("id")
        conn = db_connection()
        conn[0].execute("SELECT username,email FROM users WHERE id = %s", (userid,))
        row = conn[0].fetchone()

        key = URLSafeTimedSerializer(os.environ.get("SECRET_KEY"))
        token = key.dumps(row[1])
        url = os.environ.get("URL") + "/token/verify/" + token
        link = "<a href=" + url + ">點我啟動帳號</a>"

        # token expired time
        expired_time = str(datetime.now().replace(microsecond=0) + timedelta(minutes=30))

        # email contents:
        subject = "[你與○○的距離||custom-made-unit] 新帳號認證"
        message = row[0] + "您好，<br><br>請點選右側連結來啟動帳號："\
            + link + "<br>謝謝(`・ω・´)<br><br>提示：這個連結會在"\
            + expired_time \
            + "後過期<br>如果這封信被打開時，連結已經超過賞味期限，"\
            + "請<a href='" + os.environ.get("URL") + "/token/sent'>點此</a>來取得新的認證email"

        msg = Message(
            subject=subject,
            recipients=[row[1]],
            html=message
        )
        mail.send(msg)
        session["last"] = now + timedelta(minutes=5)

        email = validate_email(row[1])
        email_star = str(to_star(str(email["local"])) + "@" + str(email["domain"]))
        session["newtoken"] = "認證信已經發到<span class='text-primary'>"\
                              +email_star+"</span>，請依照信中說明來啟動帳號，謝謝。"
        return redirect(url_for("token_sent_done"))
    else:
        return redirect(url_for("token_sent_fail", sec=abs(int((now-last).total_seconds()))))


@app.route("/token/sent/done")
def token_sent_done():
    error = session.get("newtoken")
    return render_template("token_sent.html", error=error)


@app.route("/token/sent/fail")
def token_sent_fail():
    sec = int(request.args.get("sec"))
    minutes, seconds = divmod(sec, 60)
    if minutes == 0:
        wait_time = str(seconds)+"秒"
    else:
        wait_time = str(minutes)+"分"+str(seconds)+"秒"
    return render_template("token_sent_fail.html", error=wait_time)


@app.route("/token/verify/<token>")
def token_verify(token):
    key = URLSafeTimedSerializer(os.environ.get("SECRET_KEY"))
    try:
        plaintext = key.loads(token, max_age=1800)
    except SignatureExpired:
        return render_template("token_verify_fail.html", status="token過期")
    except BadSignature:
        return render_template("token_verify_fail.html", status="token無效")

    # check if plaintext(email) exists in db
    conn = db_connection()
    conn[0].execute("SELECT email from users where email = %s", (plaintext,))
    row = conn[0].fetchone()
    if row[0] is None:
        return render_template("token_verify_fail.html", status=None)
    else:
        conn[0].execute("UPDATE users SET verified = true WHERE email = %s", (plaintext,))
        conn[1].commit()
        session["verified"] = True
        return redirect(url_for("index", verify="true"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.clear()
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return render_template("login.html", error="登入資訊有短缺，請輸入帳號與密碼。")
        elif new_user(username) is True:
            return render_template("login.html", error="查無此帳號，請先註冊。")
        else:
            conn = db_connection()
            conn[0].execute("SELECT hash FROM users WHERE username = %s", (username,))
            row = conn[0].fetchone()
            db_password = row[0]

        if check_password_hash(db_password, password) is False:
            return render_template("login.html", error="密碼不正確")
        else:
            conn[0].execute("SELECT id,verified from users WHERE username = %s", (username,))
            row = conn[0].fetchone()
            # pack user information into session
            session["id"] = row[0]
            session["verified"] = row[1]
            return redirect(url_for("index"))
    else:
        return render_template("login.html", error=None)


@app.route("/pass/forget", methods=["GET", "POST"])
def pass_forget():
    if request.method == "POST":
        user = request.form.get("input")
        if not user:
            return render_template("pass_forget.html", error="請輸入帳號或信箱。")
        elif verify_mail(user) == "mail_invalid":
            if new_user(user) is True:
                return render_template("pass_forget.html", error="此帳號還未註冊，無法重新設定密碼。")
            else:
                conn = db_connection()
                conn[0].execute("SELECT username,email FROM users WHERE username = %s", (user,))
                row = conn[0].fetchone()
        elif verify_mail(user) == "mail_new":
            return render_template("pass_forget.html", error="此信箱還未註冊，無法重新設定密碼。")
        elif verify_mail(user) == "mail_existed":
            conn = db_connection()
            conn[0].execute("SELECT username,email FROM users WHERE email = %s", (user,))
            row = conn[0].fetchone()

        key = URLSafeSerializer(os.environ.get("SECRET_KEY"))
        token = key.dumps(row[0])
        url = os.environ.get("URL") + "/pass/reset/" + token
        link = "<a href=" + url + ">點我重置密碼</a>"

        subject = "[你與○○的距離||custom-made-unit] 密碼重置"
        message = row[0] + "你好，<br><br>請點選右側連結來重新設定密碼：" + link + "<br>謝謝(´・ω・`)<br><br>"\
            + "如果沒有重設密碼的需求，請忽略這封信，謝謝。"

        msg = Message(
            subject=subject,
            recipients=[row[1]],
            html=message
        )
        mail.send(msg)

        email = validate_email(row[1])
        email_star = str(to_star(str(email["local"])) + "@" + str(email["domain"]))
        session["newpassword"] = "重置密碼的信已經發到<span class='text-primary'>"\
                                 +email_star+"</span>，請依照信中說明來重新設定密碼，謝謝。"
        return redirect(url_for("pass_forget_sent"))
    else:
        return render_template("pass_forget.html", error=None)


@app.route("/pass/forget/sent")
def pass_forget_sent():
    error = session.get("newpassword")
    return render_template("pass_forget_sent.html", error=error)


@app.route("/pass/reset/<token>")
def pass_reset_verify(token):
    key = URLSafeSerializer(os.environ.get("SECRET_KEY"))
    try:
        plaintext = key.loads(token)
        session["reset"] = plaintext
        return redirect(url_for("pass_reset"))
    except BadSignature:
        return redirect(url_for("pass_reset"))


@app.route("/pass/reset", methods=["GET", "POST"])
def pass_reset():
    if request.method == "POST":
        username = session.get("reset")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            session.clear()
            return render_template("pass_reset.html")
        elif not password or not confirmation:
            session["error"] = "請輸入密碼與確認密碼"
            return render_template("pass_reset.html")
        elif verify_input(password) is False or verify_len(password, 8, 24) is False:
            session["error"] = "密碼不符合規範：8-24個字元，至少包含1英文字母、1數字。"
            return render_template("pass_reset.html")
        elif password != confirmation:
            session["error"] = "兩次輸入的密碼內容不同，請檢查。"
            return render_template("pass_reset.html")
        else:
            hashpass = generate_password_hash(password)
            conn = db_connection()
            conn[0].execute("UPDATE users SET hash = %s WHERE username = %s",
                               (hashpass, username))
            conn[1].commit()
            session.clear()
            return render_template("pass_reset_done.html")
    else:
        # redirect from pass_reset_verify() BadSignature
        return render_template("pass_reset.html")


@app.route("/")
@login_required
def index():
    userid = session.get("id")
    verified = session.get("verified")
    conn = db_connection()

    if not verified:
        conn[0].execute("SELECT username,email FROM users WHERE id = %s", (userid,))
        row = conn[0].fetchone()
        email = validate_email(row[1])
        email_star = str(to_star(str(email["local"])) + "@" + str(email["domain"]))
        return render_template("index.html", username=row[0], email=email_star)
    else:
        # get this month's bill(s) SUM
        today = datetime.now()
        date_start = int(str(today.year)+str(today.month)+str(0)+str(0))
        date_end = int(str(today.year)+str(today.month)+str(32))
        conn[0].execute("SELECT SUM(amount) FROM bills WHERE userid = %s \
                           AND datestamp BETWEEN %s AND %s", (userid, date_start, date_end))
        row = conn[0].fetchone()

        # in case of no bill
        if row[0] is None:
            amount = 0
        else:
            amount = row[0]

        # get target-setting status
        conn[0].execute("SELECT targetunit,target,targetamount from targets where userid = %s",
                           (userid,))
        row = conn[0].fetchone()

        # no targetamount info
        if (row[0] and row[1] and row[2]) is None:
            session["targets"] = None
            return render_template("index.html")
        else:
            session["targets"] = True
            # only display not null target(s)
            targets = [row[i] for i in range(0, 2) if row[i] is not None]
            percentage = round(float(amount)/float(row[2]), 2)
            return render_template("index.html",
                                   amount=amount, targets=targets, percentage=percentage)


@app.route("/bill/query/month", methods=["POST"])
@login_required
def bill_query_month():
    """for index.html"""
    userid = session.get("id")
    conn = db_connection()
    date_start = int("".join(request.get_json()["date"].split("-"))+str(0)+str(0))
    date_end = int("".join(request.get_json()["date"].split("-"))+str(32))
    conn[0].execute("SELECT SUM(amount) FROM bills WHERE userid = %s AND \
                       datestamp BETWEEN %s AND %s", (userid, date_start, date_end))
    row = conn[0].fetchone()

    if row[0] is None: # no bill record
        result = {"amount": 0, "percentage": 0}
        return jsonify(result)
    else:
        conn[0].execute("SELECT targetamount FROM targets WHERE userid = %s", (userid,))
        target = conn[0].fetchone()
        result = {"amount": row[0], "percentage": (row[0]/target[0])}
        return jsonify(result)


@app.route("/bill/add", methods=["GET", "POST"])
@login_required
def bill_add():
    userid = session.get("id")
    conn = db_connection()
    conn[0].execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userid,))
    row = conn[0].fetchone()
    group_name = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}

    if request.method == "POST":
        group_key = request.form.get("group")
        amount = request.form.get("amount")
        notes = request.form.get("notes")
        date_stamp = request.form.get("dateStamp")

        # error handle
        if not group_key or not amount or not date_stamp:
            return render_template("bill_add.html", group_name=group_name, error="記帳資料有缺，是否有漏填欄位？")

        try:
            # YYYY-MM-DD ==> YYYYMMDD
            datestamp = int("".join(date_stamp.split("-")))
        except AttributeError:
            return render_template("bill_add.html", group_name=group_name,
                                   error="日期格式有誤，請透過網頁日曆選取日期")
        try:
            amount_int = int(amount)
        except ValueError:
            return render_template("bill_add.html", group_name=group_name, error="記帳金額格式有誤，只能輸入正整數")
        if amount_int < 1 or amount_int > 2147483647:
            return render_template("bill_add.html", group_name=group_name, error="記帳金額有誤，最低記帳金額為1元")

        # input OK, insert into db
        conn[0].execute("INSERT INTO bills (id,userid,groupkey,amount,notes,datestamp) \
                           VALUES (DEFAULT,%s,%s,%s,%s,%s)",
                           (userid, group_key, amount_int, notes, datestamp))
        conn[1].commit()
        return redirect(url_for("index"))
    else:
        return render_template("bill_add.html", group_name=group_name, error=None)


@app.route("/bill/view")
@login_required
def bill_view():
    userid = session.get("id")
    conn = db_connection()
    conn[0].execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userid,))
    row = conn[0].fetchone()
    group_name = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]} # for bill edit usage
    return render_template("bill_view.html", group_name=group_name)


@app.route("/bill/filter", methods=["POST"])
@login_required
def bill_filter():
    userid = session.get("id")
    conn = db_connection()
    start = int("".join((request.get_json()["start"]).split("-")))
    end = int("".join((request.get_json()["end"]).split("-")))

    conn[0].execute("SELECT id,datestamp,groupkey,notes,amount FROM bills \
                       WHERE (datestamp BETWEEN %s AND %s) AND userid = %s \
                       ORDER BY datestamp", (start, end, userid))
    rows = conn[0].fetchall()

    conn[0].execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userid,))
    row = conn[0].fetchone()
    group_name = {"g0":row[0], "g1":row[1], "g2":row[2], "g3":row[3]}

    if not rows:
        return jsonify(False)
    else:
        bills = []
        for items in rows:
            table_row = []
            for i in items:
                if i in group_name:
                    # append group name according to group key
                    table_row.append(group_name[i])
                else:
                    table_row.append(i)
            bills.append(table_row)
        return jsonify(bills)


@app.route("/bill/edit", methods=["POST"])
@login_required
def bill_edit():
    bill_update = request.get_json()["content"]
    userid = bill_update["id"]
    conn = db_connection()

    for key, value in bill_update.items():
        if key == "ediDate":
            new_date = int(value)
            conn[0].execute("UPDATE bills SET datestamp = %s WHERE id = %s", (new_date, userid))
            conn[1].commit()
        if key == "ediGroup":
            conn[0].execute("UPDATE bills SET groupkey = %s WHERE id = %s", (value, userid))
            conn[1].commit()
        if key == "ediNote":
            conn[0].execute("UPDATE bills SET notes = %s WHERE id = %s", (value, userid))
            conn[1].commit()
        if key == "ediAmount":
            conn[0].execute("UPDATE bills SET amount = %s WHERE id = %s", (value, userid))
            conn[1].commit()
    return jsonify(True)


@app.route("/bill/delete", methods=["POST"])
@login_required
def bill_delete():
    bill_to_delete = request.get_json()["id"]
    conn = db_connection()
    conn[0].execute("DELETE from bills WHERE id = %s", (bill_to_delete,))
    conn[1].commit()
    return jsonify(True)


@app.route("/setting")
@login_required
def setting():
    userid = session.get("id")
    conn = db_connection()
    # pull target status from db
    conn[0].execute("SELECT target,targetamount,targetunit from targets \
                       WHERE userid = %s", (userid,))
    row = conn[0].fetchone()
    target = row[0]
    target_amount = row[1]
    target_unit = row[2]

    # pull group names from db
    conn[0].execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userid,))
    row = conn[0].fetchone()
    group_name = [row[0], row[1], row[2], row[3]]

    return render_template("setting.html", group_name=group_name,
                           target=target, target_amount=target_amount, target_unit=target_unit)


@app.route("/setting/target", methods=["POST"])
@login_required
def setting_target():
    userid = session.get("id")
    targets = request.get_json()
    conn = db_connection()
    updated_targets = {}

    for key, value in targets.items():
        if key == "targetAmount" and value:
            try:
                int(value)
            except ValueError:
                return jsonify(False)
            if int(value) > 1 and int(value) < 2147483647:
                conn[0].execute("UPDATE targets SET targetamount = %s WHERE userid = %s",
                                   (value, userid))
                conn[1].commit()
                updated_targets.update({key: value})
        if key == "target" and value and len(value) < 25:
            conn[0].execute("UPDATE targets SET target = %s WHERE userid = %s", (value, userid))
            conn[1].commit()
            updated_targets.update({key: value})
        if key == "targetUnit" and value and len(value) < 9:
            conn[0].execute("UPDATE targets SET targetunit = %s WHERE userid = %s",
                               (value, userid))
            conn[1].commit()
            updated_targets.update({key: value})

    return jsonify(updated_targets)


@app.route("/setting/group", methods=["POST"])
@login_required
def setting_group():
    userid = session.get("id")
    group_key = request.get_json()["groupKey"]
    new_group_name = request.get_json()["updateName"]
    conn = db_connection()

    if not group_key or not new_group_name or len(str(new_group_name)) > 24:
        return jsonify(False)
    else:
        conn[0].execute(f"UPDATE users SET {group_key} = %s WHERE id = %s",
                           (new_group_name, userid))
        conn[1].commit()
        # get updated group name(s)
        conn[0].execute("SELECT g0, g1, g2, g3 FROM users WHERE id = %s", (userid,))
        group_name = conn[0].fetchone()
        return jsonify(group_name)


@app.route("/setting/account", methods=["GET", "POST"])
@login_required
def setting_account():
    if request.method == "POST":
        password = request.form.get("password")
        if not password:
            return render_template("setting_account.html", error="請輸入密碼")

        userid = session.get("id")
        conn = db_connection()
        conn[0].execute("SELECT hash FROM users WHERE id = %s", (userid,))
        row = conn[0].fetchone()
        db_password = row[0]

        if check_password_hash(db_password, password) is False:
            return render_template("setting_account.html", error="密碼不正確")
        else:
            conn[0].execute("SELECT email FROM users WHERE id = %s", (userid,))
            row = conn[0].fetchone()
            email = row[0]
            return render_template("setting_account.html", email=email, verification=True)
    else:
        return render_template("setting_account.html", verification=None, error=None)


@app.route("/setting/account/pass", methods=["POST"])
@login_required
def setting_pass():
    userid = session.get("id")
    new_pass = request.get_json()["pass1"]
    new_hash = generate_password_hash(new_pass)
    conn = db_connection()
    conn[0].execute("UPDATE users SET hash = %s WHERE id = %s", (new_hash, userid))
    conn[1].commit()
    return jsonify(True)


@app.route("/setting/account/email", methods=["POST"])
@login_required
def setting_email():
    userid = session.get("id")
    new_email = request.get_json()["email"]
    conn = db_connection()
    conn[0].execute("UPDATE users SET email = %s WHERE id = %s", (new_email, userid))
    conn[1].commit()
    return jsonify(True)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


@app.errorhandler(404)
def error404(error):
    return render_template("error.html", code=404), 404


@app.errorhandler(500)
def error500(error):
    return render_template("error.html", code=500), 500
