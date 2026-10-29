import re
import sqlite3
from functools import wraps

from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint('auth', __name__)


def validate_account(name, email, password):
    name, email = name.strip(), email.strip().lower()
    errors = []
    if not 2 <= len(name) <= 80:
        errors.append('Name must be 2 to 80 characters.')
    if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        errors.append('Enter a valid email address (up to 254 characters).')
    if not 12 <= len(password) <= 128:
        errors.append('Password must be 12 to 128 characters.')
    return name, email, errors


@bp.before_app_request
def load_user():
    g.user = None
    user_id = session.get('user_id')
    if user_id is not None:
        user = get_db().execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user is None or user['is_locked'] or user['session_version'] != session.get('session_version'):
            session.clear()
            flash('Your session has ended. Please sign in again.', 'warning')
        else:
            g.user = user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user['role'] != 'Admin':
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@bp.route('/register', methods=['GET', 'POST'])
def register():
    errors = []
    if request.method == 'POST':
        name, email, errors = validate_account(request.form.get('name', ''), request.form.get('email', ''), request.form.get('password', ''))
        if request.form.get('password') != request.form.get('confirm_password'):
            errors.append('Passwords do not match.')
        if not errors:
            db = get_db()
            try:
                db.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
                           (name, email, generate_password_hash(request.form['password']), 'Customer'))
                db.commit()
            except sqlite3.IntegrityError:
                db.rollback()
                errors.append('This email is already in use.')
            else:
                flash('Your account is ready. Please sign in.', 'success')
                return redirect(url_for('auth.login'))
    return render_template('register.html', errors=errors), 400 if errors else 200


@bp.route('/login', methods=['GET', 'POST'])
def login():
    errors = []
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = get_db().execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if len(email) > 254 or not 12 <= len(password) <= 128 or user is None or not check_password_hash(user['password_hash'], password) or user['is_locked']:
            errors.append('Sign in failed. Check your email and password. Your account may be locked.')
        else:
            session.clear()
            session['user_id'] = user['id']
            session['session_version'] = user['session_version']
            return redirect(url_for('auth.account'))
    return render_template('login.html', errors=errors), 400 if errors else 200


@bp.post('/logout')
@login_required
def logout():
    session.clear()
    flash('You have signed out.', 'success')
    return redirect(url_for('home'))


@bp.get('/account')
@login_required
def account():
    return render_template('account.html')
