import datetime as dt
import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from flask.ext.moment import Moment

app = Flask(__name__)
moment = Moment(app)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'abounce.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('ABOUNCE_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute("""SELECT max(id) as id, next, location,
                    comments FROM main""")
    entries = cur.fetchall()
    then = dt.datetime.strptime(entries[0]['next'], "%Y-%m-%d %H:%M:%S")
    return render_template('main.html', entries=entries, then = then)

@app.route('/add')
def add():
    return render_template('add.html')


@app.route('/add_event', methods=['GET','POST'])
def add_event():
    db = get_db()
    next_date = request.form['nextdate']
    next_time = request.form['nexttime']
    next_dt = dt.datetime.strptime(next_date + " " + next_time,
            "%m/%d/%Y %H:%M")
    print next_dt
    db.execute('insert into main (next, location, comments) values (?, ?, ?)',
                 [next_dt, request.form['location'], request.form['comments']])
    db.commit()
    flash('New entry was successfully posted')
    return render_template('main.html')


if __name__ == '__main__':
    app.run()
