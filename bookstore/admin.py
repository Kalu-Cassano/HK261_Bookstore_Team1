import sqlite3

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from .auth import admin_required, validate_account
from .db import get_db

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.get('/accounts')
@admin_required
def accounts():
    users = get_db().execute('SELECT id, name, email, role, is_locked FROM users ORDER BY id').fetchall()
    return render_template('admin/accounts.html', users=users)


@bp.route('/accounts/new', methods=['GET', 'POST'])
@admin_required
def create_account():
    errors = []
    if request.method == 'POST':
        name, email, errors = validate_account(request.form.get('name', ''), request.form.get('email', ''), request.form.get('password', ''))
        role = request.form.get('role', '')
        if role not in ('Admin', 'Customer'):
            errors.append('Choose a valid role.')
        if request.form.get('password') != request.form.get('confirm_password'):
            errors.append('Passwords do not match.')
        if not errors:
            db = get_db()
            try:
                db.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
                           (name, email, generate_password_hash(request.form['password']), role))
                db.commit()
            except sqlite3.IntegrityError:
                db.rollback()
                errors.append('This email is already in use.')
            else:
                flash('Account created.', 'success')
                return redirect(url_for('admin.accounts'))
    return render_template('admin/create.html', errors=errors), 400 if errors else 200


@bp.post('/accounts/<int:user_id>/update')
@admin_required
def update_account(user_id):
    role, state = request.form.get('role'), request.form.get('state')
    if role not in ('Admin', 'Customer') or state not in ('active', 'locked'):
        abort(400)
    locked = int(state == 'locked')
    db = get_db()
    # Serialize the check and update so two requests cannot remove both Admins.
    db.execute('BEGIN IMMEDIATE')
    try:
        user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user is None:
            abort(404)
        active_admins = db.execute("SELECT COUNT(*) FROM users WHERE role = 'Admin' AND is_locked = 0").fetchone()[0]
        if user['role'] == 'Admin' and not user['is_locked'] and (role != 'Admin' or locked) and active_admins <= 1:
            db.rollback()
            flash('Keep at least one active Admin. This change was rejected.', 'danger')
            return redirect(url_for('admin.accounts'))
        # Locking invalidates all sessions, including after a later unlock.
        db.execute('UPDATE users SET role = ?, is_locked = ?, session_version = session_version + ? WHERE id = ?',
                   (role, locked, int(locked and not user['is_locked']), user_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    flash('Account updated.', 'success')
    return redirect(url_for('admin.accounts'))
