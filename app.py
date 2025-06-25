
import io
import base64

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
import MySQLdb.cursors
from config import Config
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config.from_object(Config)

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id_, username, email):
        self.id = id_
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user['id'], user['username'], user['email'])
    return None

@app.route('/')
def index():
    return redirect(url_for('login dulu'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered')
            return redirect(url_for('register'))
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                       (username, email, password))
        mysql.connection.commit()
        flash('Registered successfully')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        if user:
            login_user(User(user['id'], user['username'], user['email']))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    graph_url = generate_progress_graph(current_user.id)
    return render_template('dashboard.html', username=current_user.username, graph_url=graph_url)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/progress')
def progress():
    import io, base64
    import numpy as np  # Add numpy import here or at top
    
    dates = pd.date_range(start='2025-06-01', periods=7)
    data = {
        'Math': np.random.randint(70, 100, size=7),
        'Science': np.random.randint(70, 100, size=7),
        'English': np.random.randint(70, 100, size=7)
    }
    df = pd.DataFrame(data, index=dates)

    # Plot Matplotlib figure
    fig, ax = plt.subplots(figsize=(10, 5))
    df.plot(ax=ax, marker='o')
    ax.set_title('Learning Progress Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Score (%)')
    ax.set_ylim(0, 100)
    ax.grid(True)
    plt.tight_layout()

    # Save plot to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Render template with embedded image
    return render_template('progress.html', chart=image_base64)


@app.route('/courses')
def courses():
    # Sample courses data (from DB ideally)
    courses = [
        {'id': 1, 'title': 'Intro to AI', 'priority': 3, 'level': 'Beginner', 'duration': 10},
        {'id': 2, 'title': 'ML Advanced', 'priority': 5, 'level': 'Advanced', 'duration': 25},
        {'id': 3, 'title': 'Data Science', 'priority': 4, 'level': 'Intermediate', 'duration': 20},
        {'id': 4, 'title': 'NLP Basics', 'priority': 2, 'level': 'Beginner', 'duration': 12},
        {'id': 5, 'title': 'Computer Vision', 'priority': 1, 'level': 'Intermediate', 'duration': 15},
        # Add more courses...
    ]

    # Prepare DataFrame
    df = pd.DataFrame(courses)

    # Plot: Bar chart for priorities
    plt.figure(figsize=(10,6))
    plt.bar(df['title'], df['priority'], color='indigo')
    plt.xlabel('Courses')
    plt.ylabel('Priority')
    plt.title('Course Priorities')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save plot to PNG image in memory
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True)
    buf.seek(0)
    plt.close()

    # Encode PNG image to base64 string to embed directly
    plot_data = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('courses.html', courses=courses, plot_data=plot_data)


@app.route('/courses/<int:course_id>')
def course_detail(course_id):
    # your logic here
    return f"Details for course {course_id}"


def generate_progress_graph(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM progress WHERE user_id = %s", (user_id,))
    records = cursor.fetchall()
    if not records:
        return None

    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(df['date'])
    plt.figure(figsize=(10, 5))
    plt.plot(df['date'], df['math'], label='Math', marker='o')
    plt.plot(df['date'], df['science'], label='Science', marker='o')
    plt.plot(df['date'], df['english'], label='English', marker='o')
    plt.title('Learning Progress')
    plt.xlabel('Date')
    plt.ylabel('Score')
    plt.legend()
    plt.grid(True)
    graph_path = os.path.join('static', 'progress.png')
    plt.savefig(graph_path)
    plt.close()
    return '/' + graph_path

if __name__ == '__main__':
    app.run(debug=True)
