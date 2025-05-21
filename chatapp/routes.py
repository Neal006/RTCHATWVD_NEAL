from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from chatapp.forms import RegisterForm, LoginForm
from chatapp.models import User, Message
from chatapp import db
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose another.', 'danger')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use another.', 'danger')
            return redirect(url_for('main.register'))

        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/chat')
def chat():
    return render_template('chat.html', username = current_user.username)

@main.route('/search_users')
@login_required
def search_users():
    query = request.args.get('query', '')
    # Only allow alphanumeric and underscore for usernames
    if not query.isalnum() and '_' not in query:
        return jsonify([])  # or abort(400)
    users = User.query.filter(User.username.ilike(f"%{query}%")).all()
    result = [u.username for u in users if u.username != current_user.username]
    return jsonify(result)

def room_id(user1, user2):
    return '_'.join(sorted([user1,user2]))

@main.route('/chat/target_username>')
@login_required
def chat_with_user(target_username):
    if target_username == current_user.username:
        abort(403)
    return render_template('chat.html', room = room_id(current_user.username, target_username), you = current_user.username,them = target_username)
    
@main.route('/load_messages')
@login_required
def load_messages():
    user1 = current_user.username
    user2 = request.args.get('target')
    if not user2 or user2 == user1 or not User.query.filter_by(username=user2).first():
        return jsonify([])  
    room = room_id(user1, user2)
    messages = Message.query.filter_by(room=room).order_by(Message.timestamp).all()
    return jsonify([
        {
            'sender': msg.sender,
            'receiver': msg.receiver,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        for msg in messages
    ])

@main.route('/recent_chats')
@login_required
def recent_chats():
    user = current_user.username
    subq = db.session.query(
        Message.room,
        db.func.max(Message.timestamp).label('max_time')
    ).filter((Message.sender==user)|(Message.receiver==user)).group_by(Message.room).subquery()
    messages = db.session.query(Message).join(
        subq, (Message.room==subq.c.room) & (Message.timestamp==subq.c.max_time)
    ).order_by(Message.timestamp.desc()).all()
    chats = []
    for msg in messages:
        other = msg.receiver if msg.sender == user else msg.sender
        chats.append({'username': other, 'last_message': msg.content})
    return jsonify(chats)