import os
import sqlite3
import datetime
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing

DATABASE = './yatl.db'
DEBUG = True
SECRET_KEY = 'development key'
PASSWORD = os.getenv('YATL_PASSWORD') or 'PASSWORD'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('YATL_SETTINGS', silent=True)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

def update_task(task_id, status):
    post = g.db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if post is None:
        return False

    g.db.execute('UPDATE tasks SET status = ?  WHERE id = ?;', (status, task_id))
    g.db.commit()
    return True

@app.route('/', methods=['GET', 'POST'])
def show_tasks():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    cur = g.db.execute('SELECT id, time, title, description, status FROM tasks WHERE subtask_of_id IS NULL ORDER BY time DESC')
    entries = [dict(_id=row[0], time=row[1], title=row[2], description=row[3], status=row[4]) for row in cur.fetchall()]
    return render_template('show_tasks.html', entries=entries)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_tasks'))
    return render_template('login.html', error=error)

@app.route('/logout', methods=['GET', 'POST'])

def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_tasks'))

@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if not session.get('logged_in'):
        abort(403)

    error = None
    if request.method == 'POST':
        if request.form['description'] == '' or request.form['title'] == '':
            error = 'Title and description are mandatory!'
        else:
            g.db.execute('INSERT INTO tasks (time, title, description, status) VALUES (?, ?, ?, ?);', [datetime.datetime.now(), request.form['title'], request.form['description'], 'New' ])
            g.db.commit()
            return redirect(url_for('show_tasks'))

    return redirect(url_for('show_tasks'))

@app.route('/task/show/<int:task_id>', methods=['GET', 'POST'])
def show_task(task_id):
    if not session.get('logged_in'):
        abort(403)

    cur = g.db.execute('SELECT id, time, title, description, status FROM tasks WHERE id = ?;', (task_id, ))
    task = [dict(_id=row[0], time=row[1], title=row[2], description=row[3], status=row[4]) for row in cur.fetchall()]


    cur = g.db.execute('SELECT id, time, txt FROM comments WHERE task_id = ?;', (task_id, ))
    comments = [dict(_id=row[0], time=row[1], txt=row[2]) for row in cur.fetchall()]

    return render_template('task.html', task=task[0], comments=comments)

@app.route('/task/remove/<int:task_id>', methods=['GET', 'POST'])
def remove_task(task_id):
    if not session.get('logged_in'):
        abort(403)

    post = g.db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if post is None:
        abort(404, "Task id {0} doesn't exist.".format(task_id))
    g.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    g.db.commit()

    flash("Task was removed")
    return redirect(url_for('show_tasks'))

@app.route('/task/finish/<int:task_id>', methods=['GET', 'POST'])
def finish_task(task_id):
    if not session.get('logged_in'):
        abort(403)

    #  post = g.db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    #  if post is None:
    #      abort(404, "Task id {0} doesn't exist.".format(task_id))
    #
    #  g.db.execute('UPDATE tasks SET status = "Finished"  WHERE id = ?;', (task_id, ))
    #  g.db.commit()
    if update_task(task_id, "Finished"):
        flash("Task was finished")
    else:
        abort(404, "Task id {0} doesn't exist.".format(task_id))

    return redirect(url_for('show_tasks'))

@app.route('/task/in_progress/<int:task_id>', methods=['GET', 'POST'])
def progress_task(task_id):
    if not session.get('logged_in'):
        abort(403)

    if update_task(task_id, "In progress"):
        flash("Task was progressed")
    else:
        abort(404, "Task id {0} doesn't exist.".format(task_id))

    return redirect(url_for('show_tasks'))

@app.route('/task/edit/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    if not session.get('logged_in'):
        abort(403)

    post = g.db.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    if post is None:
        abort(404, "Task id {0} doesn't exist.".format(task_id))

    g.db.execute('UPDATE tasks SET title = ?, description = ?  WHERE id = ?;', (request.form["title"], request.form["description"], task_id))
    g.db.commit()

    flash("Task was edited")
    return redirect(url_for('show_tasks'))

@app.route('/task/comment/<int:task_id>', methods=['GET','POST'])
def comment_task(task_id):
    if not session.get('logged_in'):
        abort(403)
    
    g.db.execute('INSERT INTO comments (time, txt, task_id) VALUES (?, ?, ?);', [datetime.datetime.now(), request.form['txt'], task_id ])  
    g.db.commit()

    return redirect(url_for('show_task', task_id=task_id))

@app.route('/comment/remove/<int:comment_id>', methods=['GET', 'POST'])
def remove_comment(comment_id):
    if not session.get('logged_in'):
        abort(403)
    g.db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    g.db.commit()
    flash("Comment was removed")
    return redirect(url_for('show_tasks'))

if __name__ == "__main__":
    app.run()
