import sqlite3
from typing import Dict, List
from flask import Flask, render_template, request, g, session, redirect, url_for, escape

#the database file we are going to communicate with
DATABASE = 'database.db'
app = Flask(__name__)
app.secret_key = 'compatibility for mobile screens??'


# connects to the database
def get_db():
    # if there is a database, use it
    db = getattr(g, '_database', None)
    if db is None:
        # otherwise, create a database to use
        db = g._database = sqlite3.connect(DATABASE)
    return db

# converts the tuples from get_db() into dictionaries
def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
            for idx, value in enumerate(row))

# given a query, executes and returns the result
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# this function must come after the instaniation of the variable app
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        # close the database if we are connected to it
        db.close()    

# logout screen
@app.route('/')
def defaultscreen():
    session['access_username'] = ''
    session['isadmin'] = False
    return render_template('login.html')

def login_init(username, password,):
    db = get_db()
    db_cur = db.cursor()
    db_cur.execute("insert into Login values ('"+ username +"','"+ password +"')")
    db.commit()

def user_init(username, name, type_of):
    db = get_db()
    db_cur = db.cursor()
    db_cur.execute("insert into Users values ('"+ username +"','"+ name +"','"+ type_of +"')")
    db.commit()

@app.route('/signup.html', methods = ['GET', 'POST'])
@app.route('/signup')
def signup():
    db = get_db()
    db.row_factory = make_dicts
    signup_dict = []
    if request.method == 'POST':
        if request.form.get("signup") == "signup":
            if request.form.get("usertype") == "S":
                name = request.form["name"]
                username = request.form["username"]
                password = request.form["password"]
                login_init(username, password)
                user_init(username, name, '0')
                session['isadmin'] = False
                session['access_username'] = username
            elif request.form.get("usertype") == "I":
                name = request.form.get('name')
                username = request.form.get('username')
                password = request.form.get('password')
                login_init(username, password)
                user_init(username, name, '1')
                session['isadmin'] = True
                session['access_username'] = username
            return render_template("login.html")
    elif request.method == 'GET':
        return render_template('signup.html')



@app.route('/login.html', methods = ['GET', 'POST'])
@app.route('/login')
def login():
    defaultscreen()
    db = get_db()
    db.row_factory = make_dicts
    login_dict = []
    if request.method=='POST':
        # if request.form.get("signup"):
        #     return render_template("signup.html")
        if request.form.get("login-but") == 'login':
            user_set = query_db("SELECT * FROM Login NATURAL JOIN Users WHERE username = ? AND Password = ?",[request.form['username'], request.form['password']])
            if bool(user_set) is True:
                session['access_username'] = request.form['username']
                session['isadmin'] = bool(user_set[0]['type_of'])
                print(session['isadmin'])
                return render_template('index.html', isadmin = session['isadmin'], name = session['access_username'])
            else:
                return render_template('login.html')
    elif request.method=='GET':
        return render_template('login.html')

# , isadmin = session['isadmin'], name = session['access_username']

@app.route('/Grade.html', methods=['GET','POST'])
def root():
    # get the database
    db = get_db()
    # apply make_dicts (to change the result from a tuple to a dictioanry -- easier to work with)
    db.row_factory = make_dicts

    Grades = []
    # query for all Grades
    if request.method == 'GET':
        if session['isadmin']:
            for grade in query_db('select * from Grades'):
                temp2 = list()
                for remark in query_db('select * from Remark'):
                    if grade['username'] == remark['username']:
                        if remark['assignment_id'] == grade['assignment_id']:
                            temp2.append(remark['reason'])
                temp = {'reason': temp2}
                grade.update(temp)
                Grades.append(grade)

        else: 
            for grade in query_db('select * from Grades'):
                if grade['username'] == session['access_username']:
                    Grades.append(grade)
        db.close()
        return render_template('Grade.html', grade=Grades,isadmin = session['isadmin'])
    
    if request.method == 'POST':
        if session['isadmin']:
            if request.form.get('remark') == "new mark":
                student = request.form.get('student')
                ass_id = request.form['ass_id']
                new_mark = request.form['mark']
                change_grade(student, ass_id, new_mark)
                remove_remark(student, ass_id)
        if session['isadmin']:
            for grade in query_db('select * from Grades'):
                temp2 = list()
                for remark in query_db('select * from Remark'):
                    if grade['username'] == remark['username']:
                        if remark['assignment_id'] == grade['assignment_id']:
                            temp2.append(remark['reason'])
                temp = {'reason': temp2}
                grade.update(temp)
                Grades.append(grade)
        else: 
            for grade in query_db('select * from Grades'):
                if grade['username'] == session['access_username']:
                    Grades.append(grade)
        db.close()
        return render_template('Grade.html',grade=Grades,isadmin = session['isadmin'] )

def remove_remark(student,ass_id):
    db= get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM Remark WHERE username = ? AND assignment_id = ?" , (student, ass_id) )
    db.commit()

def change_grade(student,ass_id,mark):
    db= get_db()
    cur = db.cursor()
    cur.execute("UPDATE Grades SET Mark = ? WHERE username = ? AND assignment_id = ?" , (mark, student, ass_id) )
    db.commit()

def add_remark(username,real_name,ass_id,reason):
    db= get_db()
    cur = db.cursor()
    cur.execute("Insert INTO Remark VALUES ('"+ username+"','"+real_name+"','"+ ass_id+"','"+ reason+"')")
    db.commit()

@app.route('/grade')
def get_grade():
    db = get_db()
    db.row_factory = make_dicts

    Assid = request.args.get('Assignment')
    grade = query_db('select * from Grades where assignment_id = ?', [Assid], one=True)
    db.close()
    return render_template('Grade.html', grade=[grade], isadmin = session['isadmin'], name = session['access_username'])
# instructor view

@app.route('/Remark.html', methods=['GET','POST'])
def remark():
    # get the database
    db = get_db()
    # apply make_dicts (to change the result from a tuple to a dictioanry -- easier to work with)
    db.row_factory = make_dicts

    assignments = []
    # query for all Grades
    if request.method == 'GET':
        for grade in query_db('select * from Grades'):
            if grade['username'] == session['access_username']:
                assignments.append(grade)
        db.close()
        return render_template('Remark.html', assignments= assignments)

    if request.method == 'POST':
        if request.form.get('remark-but') == 'Submit-remark':
            ass_id = request.form['assignment']
            reason = request.form['reason']
            for name in query_db('select * FROM Users'):
                if name['username'] == session['access_username']:
                    real_name = name['name'] 
            add_remark(session['access_username'],real_name,ass_id,reason)
        return render_template('index.html',name = session['access_username'])

# helper function for adding feedback
def add_feedback(teaching, improve_teaching, labs, improve_labs, instructor):
    db = get_db()
    db_cur = db.cursor()
    db_cur.execute("insert into Feedback values ('"+ teaching +"','"+ improve_teaching +"','"+ labs +"','"+ improve_labs +"','"+ instructor+"')")
    db.commit()


# when user wants to go to feedback page
@app.route('/Feedback.html', methods=['GET','POST'])
def feedback():
    db = get_db()
    db.row_factory = make_dicts
    prof = []

    if request.method == 'GET':
        if session['isadmin']:
            feedbacks = []
            for back in query_db('select * from Feedback'):
                if session['access_username'] == back['instructor']:
                    feedbacks.append(back)
            return render_template('Feedback.html', feedbacks = feedbacks, isadmin = session['isadmin'])


        for user in query_db('select * from Users'):
            if(user['type_of'] == 1):
                prof.append(user)
            db.close()
        return render_template('Feedback.html', instructor = prof, isadmin = session['isadmin'])

    if request.method == 'POST':
        if request.form.get('feedback') == 'Submit Feedback':
            teaching = request.form.get('teaching')
            improve_teaching = request.form['improve_teaching']
            labs = request.form['labs']
            improve_labs = request.form['improve_labs']
            instructor = request.form["role"]
            add_feedback(teaching, improve_teaching, labs, improve_labs, instructor)
        for user in query_db('select * from Users'):
            if(user['type'] == 1):
                prof.append(user)
            db.close()
        return render_template('Feedback.html', instructor = prof, isadmin = session['isadmin'])
  


  
#Other pages
@app.route('/Additional_Resources.html')
def Additional_Resources():
    return render_template('Additional_Resources.html')

@app.route('/Course_Work.html')
def Course_Work():
    return render_template('Course_Work.html')

@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/Syllabus.html')
def Syllabus():
    return render_template('Syllabus.html')

@app.route('/Teaching_Team.html')
def Teaching_Team():
    return render_template('Teaching_Team.html')

@app.route('/Tut_Office_Hours.html')
def Tut_Office_Hours():
    return render_template('Tut_Office_Hours.html')

@app.route('/Feedback_res.html')
def Feedback_res():
    return render_template('Feedback_res.html')

if __name__ == "__main__":
    app.run(debug=True)
