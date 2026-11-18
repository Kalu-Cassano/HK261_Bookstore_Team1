"""Public catalogue and Admin book maintenance, including approved CR-01."""
import re
import sqlite3
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit

import click
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask.cli import with_appcontext

from .auth import admin_required
from .db import get_db
from .isbn import next_demo_isbn, valid_isbn

bp = Blueprint('catalog', __name__)
BOOK_SELECT = '''SELECT b.*, a.name AS author, g.name AS genre FROM books b
                 JOIN authors a ON a.id=b.author_id JOIN genres g ON g.id=b.genre_id'''


def price_value(raw):
    """Accept positive decimal amounts with at most two fractional digits."""
    if not re.fullmatch(r'\d{1,9}(?:\.\d{1,2})?', raw):
        raise ValueError('Enter a price greater than zero, with at most 2 decimal places.')
    try:
        cents = int(Decimal(raw) * 100)
    except (InvalidOperation, ValueError):
        raise ValueError('Enter a valid price.')
    if cents <= 0:
        raise ValueError('Price must be greater than zero.')
    return cents


def choices(table):
    # Only internal constant table names reach this function.
    return get_db().execute(f'SELECT * FROM {table} ORDER BY name COLLATE NOCASE').fetchall()


def filter_state(args):
    state = {k: args.get(k, '').strip() for k in ('q', 'genre', 'min_price', 'max_price')}
    errors, where, params = [], ['b.is_hidden=0'], []
    if len(state['q']) > 200:
        errors.append('Search must be at most 200 characters.')
    elif state['q']:
        # Treat SQL LIKE metacharacters as literal search text.
        term = '%' + state['q'].replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        where.append("(casefold(b.title) LIKE casefold(?) ESCAPE '\\' OR casefold(a.name) LIKE casefold(?) ESCAPE '\\' OR b.isbn LIKE ? ESCAPE '\\')")
        params.extend([term, term, term])
    if state['genre']:
        if not re.fullmatch(r'[0-9]{1,10}', state['genre']) or not get_db().execute('SELECT 1 FROM genres WHERE id=?', (int(state['genre']),)).fetchone():
            errors.append('Choose a valid genre.')
        else:
            where.append('b.genre_id=?')
            params.append(int(state['genre']))
    bounds = {}
    for key, op in [('min_price', '>='), ('max_price', '<=')]:
        if state[key]:
            try:
                # Zero is useful as a lower filter bound, though book prices must be positive.
                value = 0 if state[key] in ('0', '0.0', '0.00') else price_value(state[key])
                bounds[key] = value
                where.append(f'b.price_cents {op} ?')
                params.append(value)
            except ValueError as error:
                errors.append(str(error))
    if bounds.get('min_price', 0) > bounds.get('max_price', 99999999999):
        errors.append('Minimum price cannot exceed maximum price.')
    raw_page = args.get('page', '1')
    if not re.fullmatch(r'[0-9]{1,9}', raw_page) or int(raw_page) < 1:
        errors.append('Page must be a positive integer.')
        page = 1
    else:
        page = int(raw_page)
    return state, errors, where, params, page


@bp.get('/books')
def books():
    state, errors, where, params, page = filter_state(request.args)
    items, total = [], 0
    if not errors:
        clause = ' WHERE ' + ' AND '.join(where)
        db = get_db()
        total = db.execute('SELECT COUNT(*) FROM (' + BOOK_SELECT + clause + ')', params).fetchone()[0]
        pages = max(1, (total + 11) // 12)
        if page > pages:
            abort(404)
        items = db.execute(BOOK_SELECT + clause + ' ORDER BY b.created_at DESC, b.id DESC LIMIT 12 OFFSET ?', params + [(page - 1) * 12]).fetchall()
    pages = max(1, (total + 11) // 12)
    # Build every navigation URL from known parameters; never accept an external return URL.
    navigation = {k: v for k, v in state.items() if v}
    links = [(p, url_for('catalog.books', **navigation, page=p)) for p in range(max(1, page - 2), min(pages, page + 2) + 1)]
    return render_template('catalog/list.html', books=items, total=total, page=page, pages=pages,
                           links=links, filters=state, navigation=navigation, genres=choices('genres'), errors=errors), 400 if errors else 200


@bp.get('/books/<int:book_id>')
def detail(book_id):
    book = get_db().execute(BOOK_SELECT + ' WHERE b.id=? AND b.is_hidden=0', (book_id,)).fetchone()
    if book is None:
        abort(404)
    state, errors, _, _, page = filter_state(request.args)
    back = url_for('catalog.books', **{k: v for k, v in state.items() if v}, page=page) if not errors else url_for('catalog.books')
    return render_template('catalog/detail.html', book=book, back=back)


@bp.get('/admin/books')
@admin_required
def manage_books():
    items = get_db().execute(BOOK_SELECT + ' ORDER BY b.id DESC').fetchall()
    return render_template('catalog/manage.html', books=items)


def validate_book(form, book_id=None):
    errors = []
    data = {k: form.get(k, '').strip() for k in ('title', 'author_id', 'genre_id', 'price', 'description', 'cover_url', 'stock', 'isbn')}
    data['isbn_is_demo'] = int(form.get('isbn_is_demo') == '1' or data['isbn'].startswith('000'))
    if not valid_isbn(data['isbn']):
        errors.append('ISBN must contain exactly 13 digits (0-9).')
    elif get_db().execute('SELECT 1 FROM books WHERE isbn=? AND (? IS NULL OR id!=?)', (data['isbn'], book_id, book_id)).fetchone():
        errors.append('This ISBN is already in use, including hidden books.')
    if not 1 <= len(data['title']) <= 200:
        errors.append('Title must be 1 to 200 characters.')
    if len(data['description']) > 10000:
        errors.append('Description must be at most 10000 characters.')
    for key, table in [('author_id', 'authors'), ('genre_id', 'genres')]:
        if not re.fullmatch(r'[0-9]{1,10}', data[key]) or not get_db().execute(f'SELECT 1 FROM {table} WHERE id=?', (int(data[key]),)).fetchone():
            errors.append('Choose a valid ' + table[:-1] + '.')
    try:
        data['price_cents'] = price_value(data['price'])
    except ValueError as error:
        errors.append(str(error))
    if not re.fullmatch(r'[0-9]{1,10}', data['stock']) or int(data['stock']) > 2147483647:
        errors.append('Stock must be a non-negative integer up to 2147483647.')
    cover = data['cover_url']
    try:
        parsed = urlsplit(cover)
        valid_cover = not cover or (parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password and not any(c.isspace() for c in cover))
    except ValueError:
        valid_cover = False
    if len(cover) > 1000 or not valid_cover:
        errors.append('Cover must be an HTTPS image URL up to 1000 characters, without credentials, or empty for the local cover.')
    return data, errors


@bp.route('/admin/books/new', methods=['GET', 'POST'])
@bp.route('/admin/books/<int:book_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id=None):
    db = get_db()
    book = db.execute('SELECT * FROM books WHERE id=?', (book_id,)).fetchone() if book_id is not None else None
    if book_id is not None and book is None:
        abort(404)
    data = dict(book) if book else {}
    if book:
        data['price'] = f"{book['price_cents'] / 100:.2f}"
    errors = []
    if request.method == 'POST':
        data, errors = validate_book(request.form, book_id)
        if not errors:
            values = [data[k] for k in ('title', 'author_id', 'genre_id', 'price_cents', 'description', 'cover_url', 'stock', 'isbn', 'isbn_is_demo')]
            try:
                if book is None:
                    db.execute('INSERT INTO books(title,author_id,genre_id,price_cents,description,cover_url,stock,isbn,isbn_is_demo) VALUES(?,?,?,?,?,?,?,?,?)', values)
                else:
                    db.execute('UPDATE books SET title=?,author_id=?,genre_id=?,price_cents=?,description=?,cover_url=?,stock=?,isbn=?,isbn_is_demo=? WHERE id=?', values + [book_id])
                db.commit()
            except sqlite3.IntegrityError:
                db.rollback()
                errors.append('Book could not be saved. ISBN must be unique; check the selected author and genre.')
            else:
                flash('Book saved.', 'success')
                return redirect(url_for('catalog.manage_books'))
    return render_template('catalog/edit.html', data=data, editing=book is not None, authors=choices('authors'), genres=choices('genres'), errors=errors), 400 if errors else 200


@bp.post('/admin/books/<int:book_id>/visibility')
@admin_required
def visibility(book_id):
    state = request.form.get('is_hidden')
    if state not in ('0', '1'):
        abort(400)
    db = get_db()
    if db.execute('UPDATE books SET is_hidden=? WHERE id=?', (int(state), book_id)).rowcount != 1:
        abort(404)
    db.commit()
    flash('Book visibility updated.', 'success')
    return redirect(url_for('catalog.manage_books'))


@bp.route('/admin/metadata/<kind>', methods=['GET', 'POST'])
@admin_required
def metadata(kind):
    if kind not in ('authors', 'genres'):
        abort(404)
    db, errors = get_db(), []
    if request.method == 'POST':
        name, row_id = request.form.get('name', '').strip(), request.form.get('id', '')
        if not 2 <= len(name) <= 120:
            errors.append('Name must be 2 to 120 characters.')
        if row_id and (not re.fullmatch(r'[0-9]{1,10}', row_id) or not db.execute(f'SELECT 1 FROM {kind} WHERE id=?', (int(row_id),)).fetchone()):
            errors.append('Choose an existing entry to rename.')
        if not errors:
            try:
                if row_id:
                    db.execute(f'UPDATE {kind} SET name=? WHERE id=?', (name, int(row_id)))
                else:
                    db.execute(f'INSERT INTO {kind}(name) VALUES(?)', (name,))
                db.commit()
            except sqlite3.IntegrityError:
                db.rollback()
                errors.append('This name is already in use.')
            else:
                flash('Entry saved.', 'success')
                return redirect(url_for('catalog.metadata', kind=kind))
    return render_template('catalog/metadata.html', kind=kind, entries=choices(kind), errors=errors), 400 if errors else 200


@bp.post('/admin/metadata/<kind>/<int:row_id>/delete')
@admin_required
def delete_metadata(kind, row_id):
    if kind not in ('authors', 'genres'):
        abort(404)
    db = get_db()
    if not db.execute(f'SELECT 1 FROM {kind} WHERE id=?', (row_id,)).fetchone():
        abort(404)
    column = 'author_id' if kind == 'authors' else 'genre_id'
    # Count hidden books too: a hidden book still needs its author and genre.
    linked = db.execute(f'SELECT COUNT(*) FROM books WHERE {column}=?', (row_id,)).fetchone()[0]
    if linked:
        flash(f'Cannot delete: {linked} book(s) still use this entry. Move those books to another entry first.', 'danger')
        return redirect(url_for('catalog.metadata', kind=kind))
    db.execute(f'DELETE FROM {kind} WHERE id=?', (row_id,))
    db.commit()
    flash('Entry deleted.', 'success')
    return redirect(url_for('catalog.metadata', kind=kind))


@click.command('seed-books')
@with_appcontext
def seed_books_command():
    """Insert 36 deterministic demo books; never overwrite existing rows."""
    db = get_db()
    try:
        db.execute('BEGIN IMMEDIATE')
        count = 0
        for i in range(1, 37):
            key = f'release1-demo-{i:02d}'
            if db.execute('SELECT 1 FROM books WHERE demo_key=?', (key,)).fetchone():
                continue
            author, genre = f'Demo Author {(i - 1) % 6 + 1}', ['Fiction', 'Technology', 'History', 'Science'][(i - 1) % 4]
            db.execute('INSERT INTO authors(name) VALUES(?) ON CONFLICT(name) DO NOTHING', (author,))
            db.execute('INSERT INTO genres(name) VALUES(?) ON CONFLICT(name) DO NOTHING', (genre,))
            aid = db.execute('SELECT id FROM authors WHERE name=?', (author,)).fetchone()[0]
            gid = db.execute('SELECT id FROM genres WHERE name=?', (genre,)).fetchone()[0]
            cursor = db.execute('''INSERT INTO books(title,author_id,genre_id,price_cents,description,stock,demo_key,isbn,isbn_is_demo)
                VALUES(?,?,?,?,?,?,?,?,1) ON CONFLICT(demo_key) DO NOTHING''',
                (f'Bookstore Demo {i:02d}', aid, gid, (50000 + i * 5000) * 100,
                 f'Demo volume {i}: a reading journey through {genre.lower()}. Sample content for Release 1.0.', i % 15, key, next_demo_isbn(db)))
            count += cursor.rowcount
        db.commit()
    except Exception:
        db.rollback()
        raise
    click.echo(f'Inserted {count} demo books. Existing books and accounts were kept.')
