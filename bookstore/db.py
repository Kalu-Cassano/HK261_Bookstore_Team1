import sqlite3
from pathlib import Path

import click
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Admin', 'Customer')),
    is_locked INTEGER NOT NULL DEFAULT 0 CHECK(is_locked IN (0, 1)),
    session_version INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create missing tables without deleting existing accounts."""
    Path(current_app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    db = get_db()
    db.executescript(SCHEMA)
    click.echo('Database ready. Existing accounts were kept.')


@click.command('create-admin')
@click.option('--name', prompt='Name')
@click.option('--email', prompt='Email')
@click.password_option()
@with_appcontext
def create_admin_command(name, email, password):
    """Create an Admin using a hidden, confirmed password prompt."""
    from .auth import validate_account
    name, email, errors = validate_account(name, email, password)
    if errors:
        raise click.ClickException(' '.join(errors))
    db = get_db()
    try:
        db.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
                   (name, email, generate_password_hash(password), 'Admin'))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise click.ClickException('This email is already in use.')
    click.echo('Admin account created.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
