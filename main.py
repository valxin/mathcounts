from flask import Flask
from flask import render_template, redirect, request, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os, json

# creates a Flask application
app = Flask(__name__, template_folder='static/template')

app.secret_key = 'will set secret key'

app.config['MYSQL_HOST'] = os.environ.get("DB_HOST", "localhost")
app.config['MYSQL_USER'] = os.environ.get("DB_USER", "root")
app.config['MYSQL_PASSWORD'] = os.environ.get("DB_PWD", "")
app.config['MYSQL_DB'] = 'mathcounts'
mysql = MySQL(app)

emailUser = "juststudy.net@gmail.com"
emailPwd = os.environ.get("EMAIL_PWD", "")


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/mathcounts")
def mathcounts():
    return render_template('mathcounts.html')


@app.route("/countdown", methods=['GET', 'POST'])
def countdown():
    level = 2
    year = 2022
    start_no = 0
    if request.method == 'POST':
        level = request.form['level']
        year = request.form['year']
        start_no = int(request.form['start_no'])
        print("Level/year:  ", level, year)
        session['level'] = level
        session['year'] = year
        session['start_no'] = start_no
    else:
        level = session['level']
        year = session['year']
        start_no = int(session['start_no'])

    question_num_condition = ""
    if start_no > 0:
        question_num_condition = "AND q.question_no = " + str(start_no) + " "

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT q.question_id, q.question_no, q.question, q.answers, IFNULL(i.url, '') AS imageUrl " +
        "FROM mathcounts.questions q " +
        "LEFT JOIN mathcounts.images i ON q.question_id = i.question_id " +
        "WHERE q.level_id = % s AND q.round_id = 4 AND q.year = % s " + question_num_condition +
        "ORDER BY RAND() LIMIT 1",
        (level, year,))
    records = cursor.fetchone()

    if start_no > 0 and start_no != 80:
        session['start_no'] = start_no + 1

    return render_template('countdown.html',
                           question_id=records['question_id'],
                           question_no=records['question_no'],
                           question=records["question"],
                           answers=records["answers"],
                           imageUrl=records["imageUrl"])


@app.route('/api/timescore', methods=['POST'])
def timescore():
    user_id = session['user_id']
    if user_id is not None:
        score_data = json.loads(request.data)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO mathcounts.user_countdown (question_id,user_id,time_used,score_time,leaderboard) '
                       'VALUES (% s, % s, % s, sysdate(), 0)',
                       (score_data['question_id'], user_id, score_data['time_used'],))
        mysql.connection.commit()

    return '', 201, {"msg": "saved"}


@app.route("/api/sprint", methods=['POST'])
def sprint():
    level = 2
    year = 2022
    if request.method == 'POST':
        level = request.form['level']
        year = request.form['year']
        print("Level/year:  ", level, year)
        session['level'] = level
        session['year'] = year
    else:
        level = session['level']
        year = session['year']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT q.question, q.answers, IFNULL(i.url, '') AS imageUrl " +
        "FROM mathcounts.questions q " +
        "LEFT JOIN mathcounts.images i ON q.question_id = i.question_id " +
        "WHERE q.level_id = % s AND q.round_id = 1 AND q.year = % s "
        "ORDER BY q.question_no",
        (level, year,))
    records = cursor.fetchall()
    print("question", len(records))
    return render_template('sprint_round.html', questions=records, total=len(records))


@app.route("/api/target", methods=['POST'])
def target():
    level = 2
    year = 2023
    if request.method == 'POST':
        level = request.form['level']
        year = request.form['year']
        print("Level/year:  ", level, year)
        session['level'] = level
        session['year'] = year
    else:
        level = session['level']
        year = session['year']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT q.question, q.answers, IFNULL(i.url, '') AS imageUrl " +
        "FROM mathcounts.questions q " +
        "LEFT JOIN mathcounts.images i ON q.question_id = i.question_id " +
        "WHERE q.level_id = % s AND q.round_id = 2 AND q.year = % s "
        "ORDER BY q.question_no",
        (level, year,))
    records = cursor.fetchall()
    print("level: ", level, "question", len(records))
    return render_template('target_round.html', questions=records, total=len(records))


@app.route('/api/recordscore', methods=['POST'])
def recordscore():
    user_id = session['user_id']
    if user_id is not None:
        score_data = json.loads(request.data)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO mathcounts.user_score "
                       "(level_id,round_id,year,user_id,score,score_time,leaderboard) "
                       "VALUES (% s, % s, % s, % s, % s, sysdate(), 0)",
                       (session['level'], score_data['round_id'], session['year'], user_id, score_data['score'],))
        mysql.connection.commit()

    return '', 201, {"msg": "saved"}


@app.route("/api/contact", methods=['POST'])
def contact():
    name = request.form['name']
    email = request.form['email']
    subject = request.form['subject']
    message = request.form['message']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('INSERT INTO mathcounts.contact_message (name,email,subject,message) VALUES (% s, % s, % s, % s)',
                   (name, email, subject, message,))
    mysql.connection.commit()
    return render_template('contact.html')


@app.route("/api/signUp", methods=['POST'])
def signUp():
    name = request.form['name']
    email = request.form['email']
    pwd = request.form['pwd']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT nickname FROM mathcounts.users WHERE nickname = % s OR email = % s ", (name, email,))
    records = cursor.fetchall()

    if len(records) > 0:
        return render_template('dashboard.html', name="", email="",
                               error="Nick name or email already exist.  Please log in or try a different nick name or email.")
    else:
        hash_password = hash_pwd(pwd)
        cursor.execute('INSERT INTO mathcounts.users (nickname,email,password,active) VALUES (% s, % s, % s, 1)',
                       (name, email, hash_password,))
        mysql.connection.commit()

        cursor.execute(
            "SELECT user_id FROM mathcounts.users WHERE email = % s",
            (email,))
        record = cursor.fetchone()

        session['user_id'] = record['user_id']
        session['nickname'] = name
        session['email'] = email

        return render_template('dashboard.html', name=name, email=email, error="")


def hash_pwd(password):
    import hashlib

    hash_object = hashlib.sha256()
    hash_object.update(password.encode())
    return hash_object.hexdigest()


def send_email(recipient, subject, body):
    import smtplib

    FROM = emailUser
    TO = recipient
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, TO, SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(emailUser, emailPwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('successfully sent the mail')
    except Exception as e:
        print(e)


@app.route("/api/signin", methods=['POST'])
def signin():
    email = request.form['email']
    pwd = request.form['pwd']
    hash_password = hash_pwd(pwd)

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT user_id, nickname FROM mathcounts.users WHERE email = % s AND password = % s ", (email, hash_password,))
    records = cursor.fetchall()

    if len(records) == 1:
        session['user_id'] = records[0]['user_id']
        session['nickname'] = records[0]['nickname']
        session['email'] = email
        session.permanent = True
        return render_template('dashboard.html', name=records[0]['nickname'], email=email, error="")
    else:
        return render_template('dashboard.html', name="", email="",
                               error="Invalid email or password, please try again.")


@app.route("/api/dashboard", methods=['GET', 'POST'])
def dashboard():
    user_id = session.get('user_id')
    nickname = session.get('nickname')
    if user_id is None:
        return redirect("/#signin")
    else:
        # count down round section
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT c.time_used, DATE_FORMAT(c.score_time,'%%m/%%d/%%Y') AS score_time, "
            "CASE WHEN c.leaderboard = 1 THEN 'Yes' ELSE 'No' END as leaderboard, "
            "q.question_no, q.year, l.level "
            "FROM mathcounts.user_countdown c "
            "JOIN mathcounts.questions q ON c.question_id = q.question_id AND q.round_id = 4 "
            "JOIN mathcounts.levels l ON l.level_id = q.level_id "
            "WHERE c.user_id = % s "
            "ORDER BY l.level_id, q.year, q.question_no",
            (user_id,))
        countdowns = cursor.fetchall()

        cursor.execute(
            "SELECT s.score, DATE_FORMAT(s.score_time,'%%m/%%d/%%Y') AS score_time,  "
            "CASE WHEN s.leaderboard = 1 THEN 'Yes' ELSE 'No' END as leaderboard, s.year, l.level "
            "FROM mathcounts.user_score s "
            "JOIN mathcounts.levels l ON l.level_id = s.level_id "
            "WHERE s.user_id = % s AND s.round_id = 1 "
            "ORDER BY l.level_id, s.year, s.score_time",
            (user_id,))
        sprints = cursor.fetchall()

        cursor.execute(
            "SELECT s.score, DATE_FORMAT(s.score_time,'%%m/%%d/%%Y') AS score_time,  "
            "CASE WHEN s.leaderboard = 1 THEN 'Yes' ELSE 'No' END as leaderboard, s.year, l.level "
            "FROM mathcounts.user_score s "
            "JOIN mathcounts.levels l ON l.level_id = s.level_id "
            "WHERE s.user_id = % s AND s.round_id = 2 "
            "ORDER BY l.level_id, s.year, s.score_time",
            (user_id,))
        targets = cursor.fetchall()

        return render_template('dashboard.html',
                               name=nickname,
                               countdowns=countdowns,
                               sprints=sprints,
                               targets=targets,
                               error="")


@app.route("/api/leaderboard", methods=['GET', 'POST'])
def leaderboard():
    # count down round section
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "WITH score_analysis "
        "AS ( "
        "SELECT q.year, l.level, q.question_no, c.time_used, u.nickname, "
        "row_number() OVER ( "
        "PARTITION BY q.year, l.level "
        "ORDER BY c.time_used, q.question_no desc, c.user_id "
        ") AS row_num "
        "FROM mathcounts.user_countdown c "
        "JOIN mathcounts.questions q ON c.question_id = q.question_id "
        "JOIN mathcounts.levels l ON l.level_id = q.level_id "
        "JOIN mathcounts.users u ON u.user_id = c.user_id "
        "WHERE q.round_id = 4 "
        ") "
        "SELECT year, level, question_no, time_used, nickname, row_num "
        "FROM score_analysis "
        "WHERE row_num <=10 "
        "ORDER BY year DESC, level, row_num ",
        ())
    countdowns = cursor.fetchall()

    cursor.execute(
        "WITH score_analysis "
        "AS ( "
        "SELECT c.year, l.level, c.score, u.nickname, "
        "row_number() OVER ( "
        "PARTITION BY c.year, l.level "
        "ORDER BY c.score desc, c.user_id "
        ") AS row_num "
        "FROM mathcounts.user_score c "
        "JOIN mathcounts.levels l ON l.level_id = c.level_id "
        "JOIN mathcounts.users u ON u.user_id = c.user_id "
        "WHERE c.round_id = 1 "
        ") "
        "SELECT year, level, score, nickname, row_num "
        "FROM score_analysis "
        "WHERE row_num <=5 "
        "ORDER BY year DESC, level, row_num ",
        ())
    sprints = cursor.fetchall()

    cursor.execute(
        "WITH score_analysis "
        "AS ( "
        "SELECT c.year, l.level, c.score, u.nickname, "
        "row_number() OVER ( "
        "PARTITION BY c.year, l.level "
        "ORDER BY c.score desc, c.user_id "
        ") AS row_num "
        "FROM mathcounts.user_score c "
        "JOIN mathcounts.levels l ON l.level_id = c.level_id "
        "JOIN mathcounts.users u ON u.user_id = c.user_id "
        "WHERE c.round_id = 2 "
        ") "
        "SELECT year, level, score, nickname, row_num "
        "FROM score_analysis "
        "WHERE row_num <=5 "
        "ORDER BY year DESC, level, row_num ",
        ())
    targets = cursor.fetchall()

    return render_template('leaderboard.html',
                           countdowns=countdowns,
                           sprints=sprints,
                           targets=targets,
                           error="")


# run the application
if __name__ == "__main__":
    app.run(debug=False)
