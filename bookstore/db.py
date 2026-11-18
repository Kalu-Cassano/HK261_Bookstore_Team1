import sqlite3
from pathlib import Path
from uuid import uuid4

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
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(trim(name)) BETWEEN 2 AND 120)
);
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(trim(name)) BETWEEN 2 AND 120)
);
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
    author_id INTEGER NOT NULL REFERENCES authors(id),
    genre_id INTEGER NOT NULL REFERENCES genres(id),
    price_cents INTEGER NOT NULL CHECK(typeof(price_cents) = 'integer' AND price_cents > 0 AND price_cents <= 99999999999),
    description TEXT NOT NULL DEFAULT '',
    cover_url TEXT NOT NULL DEFAULT '',
    stock INTEGER NOT NULL DEFAULT 0 CHECK(typeof(stock) = 'integer' AND stock BETWEEN 0 AND 2147483647),
    is_hidden INTEGER NOT NULL DEFAULT 0 CHECK(is_hidden IN (0, 1)),
    demo_key TEXT UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    isbn TEXT NOT NULL UNIQUE CHECK(typeof(isbn) = 'text' AND length(isbn) = 13 AND length(CAST(isbn AS BLOB)) = 13 AND isbn NOT GLOB '*[^0-9]*'),
    isbn_is_demo INTEGER NOT NULL DEFAULT 0 CHECK(isbn_is_demo IN (0, 1)),
    CHECK(substr(isbn, 1, 3) != '000' OR isbn_is_demo = 1)
);
CREATE INDEX IF NOT EXISTS books_visible_newest ON books(is_hidden, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS books_genre_price ON books(genre_id, price_cents);
'''


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
        g.db.create_function('casefold', 1, lambda value: value.casefold() if value else '', deterministic=True)
    return g.db


def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def upgrade_database(db):
    """Back up legacy databases, then atomically backfill and constrain ISBN."""
    from .isbn import demo_isbn
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    columns = [row['name'] for row in db.execute('PRAGMA table_info(books)')]
    legacy = 'books' in tables and 'isbn' not in columns
    if tables and (legacy or 'books' not in tables):
        folder = Path(current_app.config['DATABASE']).resolve().parent / 'backups'
        folder.mkdir(parents=True, exist_ok=True)
        backup = folder / f'before-cr01-{uuid4().hex}.sqlite3'
        with sqlite3.connect(backup) as target:
            db.backup(target)
        # Keep CLI output encodable on Windows cp1258 consoles even when the
        # project/database lives in a Vietnamese path.
        click.echo(f'Backup saved beside database: backups/{backup.name}')
    # Foreign keys are checked before commit. Disabling them during the table swap
    # prevents deleting related records if future tables reference books.
    db.execute('PRAGMA foreign_keys = OFF')
    try:
        db.execute('BEGIN IMMEDIATE')
        if legacy:
            definition = SCHEMA.split('CREATE TABLE IF NOT EXISTS books (', 1)[1].split('\n);', 1)[0]
            expected = {'id', 'title', 'author_id', 'genre_id', 'price_cents', 'description',
                        'cover_url', 'stock', 'is_hidden', 'demo_key', 'created_at'}
            if set(columns) != expected:
                raise RuntimeError('Unexpected legacy book columns; migration stopped to preserve data.')
            rows = db.execute('SELECT * FROM books ORDER BY id').fetchall()
            sequence = db.execute("SELECT seq FROM sqlite_sequence WHERE name='books'").fetchone()
            extras = [row[0] for row in db.execute("SELECT sql FROM sqlite_master WHERE tbl_name='books' AND type IN ('index','trigger') AND sql IS NOT NULL")]
            db.execute('CREATE TABLE books_cr01 (' + definition + '\n)')
            used = set()
            for row in rows:
                code = demo_isbn(used)
                used.add(code)
                names = columns + ['isbn', 'isbn_is_demo']
                db.execute(f"INSERT INTO books_cr01 ({','.join(names)}) VALUES ({','.join('?' for _ in names)})", tuple(row) + (code, 1))
            # All populated rows pass NOT NULL / UNIQUE / CHECK before swapping.
            db.execute('DROP TABLE books')
            db.execute('ALTER TABLE books_cr01 RENAME TO books')
            if sequence:
                db.execute("UPDATE sqlite_sequence SET seq=max(seq,?) WHERE name='books'", (sequence[0],))
            for statement in extras:
                db.execute(statement)
            click.echo(f'Backfilled {len(rows)} books with explicitly marked demo ISBN codes.')
        for statement in SCHEMA.split(';'):
            if statement.strip():
                db.execute(statement)
        if db.execute('PRAGMA foreign_key_check').fetchone() is not None:
            raise RuntimeError('Foreign key check failed; migration rolled back.')
        db.execute('PRAGMA user_version = 1')
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.execute('PRAGMA foreign_keys = ON')


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create missing tables without deleting existing accounts."""
    Path(current_app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    db = get_db()
    upgrade_database(db)
    click.echo('Database ready with CR-01. Existing accounts and book data were kept.')


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
    app.cli.add_command(init_db_command, 'upgrade-db')
    from .catalog import seed_books_command
    app.cli.add_command(seed_books_command)
    from .real_books import seed_real_books_command
    app.cli.add_command(seed_real_books_command)
