from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.permanent_session_lifetime = timedelta(minutes=5)

db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    active = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Todolist', backref=db.backref('user', lazy=True))

    def __repr__(self):
        return f'{self.username}'

class Todolist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_to_complete = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return '<Task %r>' % self.id

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        return redirect(url_for('sign_up'))
    else:
        return render_template('index.html', signup=False, login=False, logout=True)

@app.route('/view')
def view():
    return render_template('view.html', values=Users.query.all())

@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        user = Users.query.filter_by(username=username).first()
        if user:
            flash('Unavailable username! Please try another one!')
            return render_template('sign_up.html')
        password1 = request.form['password1']
        password2 = request.form['password2']
        if password1 == password2:
            user = Users(username=username, password=request.form['password1'])
            db.session.add(user)
            db.session.commit()
            sign_up = True
            flash('Sign up sucessfully!')
            return redirect(url_for('login'))
        else:
            flash('Unmatched password!')
            return render_template('sign_up.html', signup=False, login=False, logout=True, home=False)
    else:
        return render_template('sign_up.html', signup=True, login=False, logout=True, home=False)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        session.permanent = True
        username = request.form['username']
        user = Users.query.filter_by(username=username).first()
        if user:
            session['user'] = username
            password = request.form['password']
            password_check = user.password
            if password == password_check:
                flash('Log in sucessfully!')
                return redirect(url_for('user'))
            else:
                flash('Wrong password!')
                return render_template('login.html', signup=False, login=False, logout=True, home=False)
        else:
            flash('Unvalid username!')
            return render_template('login.html', signup=False, login=False, logout=True, home=False)
    else:
        if 'user' in session:
            return redirect(url_for('user'))
        return render_template('login.html', signup=False, login=False, logout=True, home=False)

@app.route('/user', methods=['POST', 'GET'])
def user():
    if 'user' in session:
        username = session['user']
        user = Users.query.filter_by(username=username).first()
        if request.method == 'POST':
            content = request.form['content']
            if content == '':
                return redirect('/user')
            date = request.form['date']
            if date == '':
                date = 'Anytime'
            new_task = Todolist(content=content, date_to_complete=date, user=user)
            try:
                db.session.add(new_task)
                db.session.commit()
                return redirect('/user')
            except:
                return 'There was an issue add new task'
        else:
            tasks = user.tasks
            return render_template('user.html', tasks=tasks, signup=True, login=True, logout=False, home=True)
    else:
        flash("You're not logged in")
        return redirect(url_for('login'))
        
@app.route('/logout')
def logout():
    if 'user' in session:
        user = session['user']
        flash(f'You have logged out, {user}')
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todolist.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/user')
    except:
        return 'There was an issue deleting the task'

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todolist.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/user')
        except:
            return 'There was an issue updating the task'
    else:
        return render_template('update.html', task=task, signup=True, login=True, logout=False, home=True)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)