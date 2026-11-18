import html
import re
import sqlite3
import os
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

import pytest

from bookstore import create_app
from bookstore.db import SCHEMA, get_db
from conftest import login, post


@pytest.fixture
def isbn_app(app):
    for command in ('seed-books', 'seed-real-books'):
        result = app.test_cli_runner().invoke(args=[command])
        assert result.exit_code == 0, result.output
    return app


def data(app, **changes):
    with app.app_context():
        row = get_db().execute('SELECT * FROM books WHERE id=1').fetchone()
        form = dict(title='New ISBN book', author_id=str(row['author_id']), genre_id=str(row['genre_id']),
                    price='230000', stock='4', cover_url='', description='Test', isbn='9780000000018')
    return {**form, **changes}


@pytest.mark.parametrize('code', ['', '123456789012', '12345678901234', '123456789012X', '１２３４５６７８９０１２３', '123-4567890123', '123456 7890123'])
def test_isbn_invalid_create_and_edit(isbn_app, client, code):
    login(client)
    for path in ('/admin/books/new', '/admin/books/1/edit'):
        response = post(client, path, data(isbn_app, isbn=code))
        assert response.status_code == 400
        assert 'exactly 13 digits' in response.text
    with isbn_app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM books').fetchone()[0] == 52


def test_duplicate_hidden_isbn_rejected_but_same_book_can_keep_it(isbn_app, client):
    login(client)
    with isbn_app.app_context():
        db = get_db()
        code = db.execute('SELECT isbn FROM books WHERE id=1').fetchone()[0]
        db.execute('UPDATE books SET is_hidden=1 WHERE id=1')
        db.commit()
    for path in ('/admin/books/new', '/admin/books/2/edit'):
        response = post(client, path, data(isbn_app, isbn=code))
        assert response.status_code == 400 and 'already in use' in response.text
    assert post(client, '/admin/books/1/edit', data(isbn_app, isbn=code)).status_code == 302
    with isbn_app.app_context():
        row = get_db().execute('SELECT * FROM books WHERE id=1').fetchone()
        assert row['isbn'] == code and row['is_hidden'] == 1 and row['isbn_is_demo'] == 1


def test_isbn_create_update_form_detail_and_demo_label(isbn_app, client):
    login(client)
    form = client.get('/admin/books/new').text
    assert 'pattern="[0-9]{13}"' in form and 'inputmode="numeric"' in form
    assert re.search(r'name="isbn"[^>]*required', form)
    assert post(client, '/admin/books/new', data(isbn_app, isbn='0009999999999')).status_code == 302
    with isbn_app.app_context():
        row = get_db().execute('SELECT * FROM books ORDER BY id DESC LIMIT 1').fetchone()
        book_id = row['id']
        assert row['isbn_is_demo'] == 1
    detail = client.get(f'/books/{book_id}').text
    assert '0009999999999' in detail and 'Demo code — not a verified edition ISBN' in detail
    assert post(client, f'/admin/books/{book_id}/edit', data(isbn_app)).status_code == 302
    detail = client.get(f'/books/{book_id}').text
    assert '9780000000018' in detail and 'Demo code — not a verified edition ISBN' not in detail
    edit = client.get(f'/admin/books/{book_id}/edit').text
    assert 'value="9780000000018"' in edit


def test_isbn_search_keeps_filters_pagination_and_back_link(isbn_app, client):
    with isbn_app.app_context():
        db = get_db()
        row = db.execute("SELECT * FROM books WHERE title='Bitcoin Is for Everyone'").fetchone()
        code, gid, book_id = row['isbn'], row['genre_id'], row['id']
    query = {'q': code, 'genre': str(gid), 'min_price': '464550', 'max_price': '464550', 'page': '1'}
    response = client.get('/books', query_string=query)
    assert response.status_code == 200 and 'Bitcoin Is for Everyone' in response.text
    assert response.text.count('class="book-cover"') == 1
    link = html.unescape(re.search(r'href="([^"]*/books/\d+[^\"]*)"', response.text).group(1))
    detail = client.get(link)
    back = html.unescape(re.search(r'id="back-to-books" href="([^"]+)"', detail.text).group(1))
    assert parse_qs(urlsplit(back).query) == {k:[v] for k,v in query.items()}
    # Demo ISBN prefix matches 52 books; page 2 and its detail links keep the query.
    page = client.get('/books?q=000&page=2')
    assert page.status_code == 200 and page.text.count('class="book-cover"') == 12
    assert 'q=000' in html.unescape(page.text)
    assert 'No books found' in client.get('/books', query_string={**query,'max_price':'464549','min_price':''}).text
    with isbn_app.app_context():
        get_db().execute('UPDATE books SET is_hidden=1 WHERE id=?',(book_id,))
        get_db().commit()
    assert 'No books found' in client.get('/books', query_string={'q':code}).text
    assert client.get(f'/books/{book_id}').status_code == 404


@pytest.mark.parametrize('code', [None, '', '1'*12, '1'*14, 'x'*13, '１'*13, '1234567890123\x00hidden', sqlite3.Binary(b'1234567890123')])
def test_sqlite_rejects_invalid_isbn(isbn_app, code):
    with isbn_app.app_context():
        db = get_db()
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('UPDATE books SET isbn=? WHERE id=1',(code,))
        db.rollback()


def test_sqlite_unique_and_demo_flag_and_seeds_preserve_codes(isbn_app):
    with isbn_app.app_context():
        db = get_db()
        code = db.execute('SELECT isbn FROM books WHERE id=1').fetchone()[0]
        for sql, args in [('UPDATE books SET isbn=? WHERE id=2',(code,)),
                          ('UPDATE books SET isbn_is_demo=0 WHERE id=1',())]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(sql,args)
            db.rollback()
        before = [tuple(r) for r in db.execute('SELECT * FROM books ORDER BY id')]
        assert len({r['isbn'] for r in db.execute('SELECT isbn FROM books')}) == 52
    for command in ('seed-books', 'seed-real-books', 'seed-books', 'seed-real-books'):
        result = isbn_app.test_cli_runner().invoke(args=[command])
        assert result.exit_code == 0 and 'Inserted 0' in result.output
    with isbn_app.app_context():
        assert [tuple(r) for r in get_db().execute('SELECT * FROM books ORDER BY id')] == before


def test_legacy_52_book_migration_backup_preservation_and_sequence(tmp_path):
    path = tmp_path/'legacy.sqlite3'
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.split('CREATE TABLE IF NOT EXISTS books (')[0])
    conn.executescript('''CREATE TABLE books (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, author_id INTEGER NOT NULL REFERENCES authors(id),
        genre_id INTEGER NOT NULL REFERENCES genres(id), price_cents INTEGER NOT NULL,
        description TEXT NOT NULL DEFAULT '', cover_url TEXT NOT NULL DEFAULT '', stock INTEGER NOT NULL DEFAULT 0,
        is_hidden INTEGER NOT NULL DEFAULT 0, demo_key TEXT UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX custom_title ON books(title);
        INSERT INTO authors(name) VALUES('Existing author'); INSERT INTO genres(name) VALUES('Existing genre');
        INSERT INTO users(name,email,password_hash,role) VALUES('Existing','existing@example.com','unchanged-hash','Customer');''')
    for i in range(1,53):
        conn.execute('INSERT INTO books(title,author_id,genre_id,price_cents,stock,is_hidden) VALUES(?,1,1,?,?,?)',
                     (f'Existing {i}',23000000+i,i,i%2))
    conn.execute("INSERT INTO books(id,title,author_id,genre_id,price_cents) VALUES(100,'Deleted',1,1,100)")
    conn.execute('DELETE FROM books WHERE id=100')
    conn.commit()
    before = {t:conn.execute(f'SELECT * FROM {t} ORDER BY id').fetchall() for t in ('books','users','authors','genres')}
    conn.close()
    app = create_app({'TESTING':True, 'SECRET_KEY':'test-only','DATABASE':str(path)})
    result=app.test_cli_runner().invoke(args=['upgrade-db'])
    assert result.exit_code==0,result.output
    assert 'Backfilled 52' in result.output
    backups=list((tmp_path/'backups').glob('before-cr01-*.sqlite3'))
    assert len(backups)==1
    with sqlite3.connect(backups[0]) as backup:
        assert backup.execute('SELECT * FROM books ORDER BY id').fetchall()==before['books']
        assert 'isbn' not in [r[1] for r in backup.execute('PRAGMA table_info(books)')]
    with app.app_context():
        db=get_db()
        for table in ('users','authors','genres'):
            assert [tuple(r) for r in db.execute(f'SELECT * FROM {table} ORDER BY id')]==before[table]
        migrated=db.execute('SELECT * FROM books ORDER BY id').fetchall()
        assert [tuple(r)[:11] for r in migrated]==before['books']
        assert all(r['isbn_is_demo']==1 and re.fullmatch('[0-9]{13}',r['isbn']) for r in migrated)
        assert len({r['isbn'] for r in migrated})==52
        assert db.execute("SELECT 1 FROM sqlite_master WHERE name='custom_title'").fetchone()
        assert db.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert db.execute("SELECT seq FROM sqlite_sequence WHERE name='books'").fetchone()[0]==100
        saved=[tuple(r) for r in migrated]
    result=app.test_cli_runner().invoke(args=['upgrade-db'])
    assert result.exit_code==0,result.output
    with app.app_context():
        assert [tuple(r) for r in get_db().execute('SELECT * FROM books ORDER BY id')]==saved
    assert len(list((tmp_path/'backups').glob('*.sqlite3')))==1


def test_windows_cli_backup_with_vietnamese_path_and_cp1258(tmp_path):
    folder=tmp_path/'Cơ sở dữ liệu'
    folder.mkdir()
    path=folder/'old.sqlite3'
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.split('CREATE TABLE IF NOT EXISTS authors')[0])
    env={**os.environ, 'DATABASE':str(path), 'SECRET_KEY':'cli-test-only', 'PYTHONIOENCODING':'cp1258'}
    result=subprocess.run([sys.executable,'-m','flask','--app','bookstore','upgrade-db'],
                          env=env,capture_output=True)
    assert result.returncode==0,result.stderr.decode('cp1258',errors='replace')
    assert b'Backup saved beside database: backups/' in result.stdout
    assert len(list((folder/'backups').glob('*.sqlite3')))==1
