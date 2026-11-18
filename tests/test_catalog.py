import html
import re
import sqlite3
from urllib.parse import parse_qs, urlsplit

import pytest

from bookstore import create_app
from bookstore.db import get_db
from conftest import login, post


@pytest.fixture
def seeded(app):
    result = app.test_cli_runner().invoke(args=['seed-books'])
    assert result.exit_code == 0, result.output
    return app


def book_data(app, **changes):
    with app.app_context():
        aid = get_db().execute('SELECT id FROM authors ORDER BY id LIMIT 1').fetchone()[0]
        gid = get_db().execute('SELECT id FROM genres ORDER BY id LIMIT 1').fetchone()[0]
    return dict(title='A New Book', author_id=str(aid), genre_id=str(gid), price='125000.50',
                stock='3', description='A useful book.', cover_url='', isbn='9780000000001', **changes)


def rows(app, query='SELECT * FROM books ORDER BY id', params=()):
    with app.app_context():
        return [dict(row) for row in get_db().execute(query, params).fetchall()]


def test_seed_idempotent_preserves_edits_and_accounts(seeded):
    before = rows(seeded, 'SELECT * FROM users')
    with seeded.app_context():
        get_db().execute("UPDATE books SET title='Custom edit', is_hidden=1, stock=7 WHERE id=1")
        get_db().commit()
    result = seeded.test_cli_runner().invoke(args=['seed-books'])
    assert result.exit_code == 0 and 'Inserted 0' in result.output
    assert len(rows(seeded)) == 36
    assert len(rows(seeded, 'SELECT * FROM authors')) == 6
    assert len(rows(seeded, 'SELECT * FROM genres')) == 4
    assert rows(seeded)[0]['title'] == 'Custom edit'
    assert rows(seeded)[0]['is_hidden'] == 1
    assert rows(seeded, 'SELECT * FROM users') == before


@pytest.mark.parametrize('path', ['/admin/books', '/admin/books/new', '/admin/books/1/edit', '/admin/metadata/authors', '/admin/metadata/genres'])
def test_admin_get_permissions(seeded, client, path):
    assert client.get(path).status_code == 302
    login(client, 'reader@example.com')
    assert client.get(path).status_code == 403
    login(client)
    assert client.get(path).status_code == 200


@pytest.mark.parametrize('path,data', [
    ('/admin/books/new', {}), ('/admin/books/1/edit', {'title': 'Hacked'}),
    ('/admin/books/1/visibility', {'is_hidden': '1'}),
    ('/admin/metadata/authors', {'name': 'Attacker'}),
    ('/admin/metadata/genres', {'name': 'Attacker'}),
])
def test_admin_post_permissions(seeded, client, path, data):
    before = rows(seeded)
    assert post(client, path, data).status_code == 302
    login(client, 'reader@example.com')
    assert post(client, path, data, page='/account').status_code == 403
    assert rows(seeded) == before


@pytest.mark.parametrize('path', ['/admin/books/new', '/admin/books/1/edit', '/admin/books/1/visibility', '/admin/metadata/authors', '/admin/metadata/genres'])
@pytest.mark.parametrize('token', ['', 'bad-token'])
def test_catalog_csrf(seeded, client, path, token):
    login(client)
    before = rows(seeded)
    assert client.post(path, data={'csrf_token': token}).status_code == 400
    assert rows(seeded) == before


def test_create_edit_hide_restore(seeded, client):
    login(client)
    data = book_data(seeded)
    assert post(client, '/admin/books/new', data).status_code == 302
    book = rows(seeded)[-1]
    assert book['price_cents'] == 12500050
    assert book['stock'] == 3
    url = f"/admin/books/{book['id']}/edit"
    assert post(client, url, {**data, 'title': 'Edited Book', 'stock': '0'}).status_code == 302
    assert 'Out of stock' in client.get(f"/books/{book['id']}").text
    visibility = f"/admin/books/{book['id']}/visibility"
    assert post(client, visibility, {'is_hidden': '1'}).status_code == 302
    assert client.get(f"/books/{book['id']}").status_code == 404
    assert 'Edited Book' not in client.get('/books?q=Edited').text
    assert rows(seeded)[-1]['is_hidden'] == 1
    assert post(client, visibility, {'is_hidden': '0'}).status_code == 302
    assert client.get(f"/books/{book['id']}").status_code == 200
    assert client.get(visibility).status_code == 405


@pytest.mark.parametrize('field,value', [
    ('title', ''), ('title', ' '), ('title', 'x'*201),
    ('price', '0'), ('price', '-1'), ('price', 'NaN'), ('price', 'Infinity'),
    ('price', '1.001'), ('price', '1e6'), ('price', '1000000000'),
    ('stock', '-1'), ('stock', '1.5'), ('stock', 'NaN'), ('stock', '2147483648'), ('stock', ''),
    ('author_id', '9999'), ('author_id', 'x'), ('genre_id', '9999'), ('genre_id', ''),
    ('cover_url', 'javascript:alert(1)'), ('cover_url', 'http://example.com/a.png'),
    ('cover_url', 'https://user:password@example.com/cover'), ('cover_url', 'https://['),
    ('description', 'x'*10001),
])
def test_invalid_books_rejected_for_create_and_edit(seeded, client, field, value):
    login(client)
    before = rows(seeded)
    data = {**book_data(seeded), field: value}
    assert post(client, '/admin/books/new', data).status_code == 400
    assert post(client, '/admin/books/1/edit', data).status_code == 400
    assert rows(seeded) == before


@pytest.mark.parametrize('kind', ['authors', 'genres'])
def test_metadata_management(seeded, client, kind):
    login(client)
    path = f'/admin/metadata/{kind}'
    assert post(client, path, {'name': 'New Entry'}).status_code == 302
    entry = rows(seeded, f"SELECT * FROM {kind} WHERE name='New Entry'")[0]
    assert post(client, path, {'id': str(entry['id']), 'name': 'Renamed'}).status_code == 302
    assert post(client, path, {'name': 'renamed'}).status_code == 400
    assert post(client, path, {'name': ' '}).status_code == 400
    assert post(client, path, {'id': '99999', 'name': 'Missing'}).status_code == 400
    assert len(rows(seeded, f"SELECT * FROM {kind} WHERE name='Renamed'")) == 1


def test_anonymous_pagination_newest_first_and_hidden(seeded, client):
    for page in range(1, 4):
        response = client.get(f'/books?page={page}')
        assert response.status_code == 200
        ids = re.findall(r'data-book-id="(\d+)"', response.text)
        assert [int(i) for i in ids] == list(range(48 - page*12, 36 - page*12, -1))
        assert response.text.count('class="book-cover"') == 12
    assert client.get('/books?page=4').status_code == 404
    with seeded.app_context():
        get_db().execute('UPDATE books SET is_hidden=1 WHERE id=36')
        get_db().commit()
    assert 'data-book-id="36"' not in client.get('/books').text
    assert client.get('/books/36').status_code == 404
    assert client.get('/books/99999').status_code == 404
    assert 'unavailable' in client.get('/books/99999').text


def test_combined_search_filter_paging_and_back_link(seeded, client):
    # Force 25 matching books to exercise multiple pages of the same combination.
    with seeded.app_context():
        db = get_db()
        db.execute("UPDATE books SET title='Combined Story', author_id=1, genre_id=1, price_cents=10000000 WHERE id<=25")
        db.commit()
    query = {'q': 'Combined', 'genre': '1', 'min_price': '99999', 'max_price': '100001', 'page': '2'}
    response = client.get('/books', query_string=query)
    assert response.status_code == 200
    assert response.text.count('class="book-cover"') == 12
    link = html.unescape(re.search(r'href="([^"]*?/books/\d+[^\"]*)"', response.text).group(1))
    detail = client.get(link)
    assert detail.status_code == 200
    back = html.unescape(re.search(r'id="back-to-books" href="([^"]+)"', detail.text).group(1))
    assert parse_qs(urlsplit(back).query) == {k: [v] for k,v in query.items()}
    assert client.get(back).text == response.text
    next_link = html.unescape(re.search(r'rel="next" href="([^"]+)"', response.text).group(1))
    assert parse_qs(urlsplit(next_link).query)['q'] == ['Combined']
    assert client.get(next_link).text.count('class="book-cover"') == 1
    assert 'No books found' in client.get('/books?q=Combined&min_price=100001').text
    assert 'No books found' in client.get('/books?q=Combined&genre=2').text


def test_author_unicode_literal_search_and_escape(seeded, client):
    with seeded.app_context():
        db = get_db()
        db.execute("UPDATE authors SET name='Nguyễn Ánh' WHERE id=1")
        db.execute("UPDATE books SET title='<script>100%_Book</script>' WHERE id=1")
        db.commit()
    assert 'data-book-id="1"' in client.get('/books?q=NGUYỄN').text
    response = client.get('/books', query_string={'q': '%_'})
    assert response.text.count('class="book-cover"') == 1
    assert '&lt;script&gt;' in response.text
    assert '<script>100%' not in response.text
    assert 'No books found' in client.get('/books', query_string={'q': "' OR 1=1 --"}).text
    assert 'evil.example' not in client.get('/books/1?next=https://evil.example').text


@pytest.mark.parametrize('query', ['page=0', 'page=-1', 'page=x', 'page=999999999999999', 'genre=xxx', 'genre=999', 'min_price=-1', 'max_price=NaN', 'min_price=2&max_price=1', 'q=' + 'x'*201])
def test_invalid_filters(seeded, client, query):
    assert client.get('/books?' + query).status_code == 400


def test_invalid_targets_and_states(seeded, client):
    login(client)
    assert client.get('/admin/books/999/edit').status_code == 404
    assert post(client, '/admin/books/999/visibility', {'is_hidden': '1'}).status_code == 404
    assert post(client, '/admin/books/1/visibility', {'is_hidden': '2'}).status_code == 400
    assert client.get('/admin/metadata/users').status_code == 404


def test_upgrade_legacy_database_preserves_all_user_columns(tmp_path):
    from bookstore.db import SCHEMA
    path = tmp_path / 'legacy.sqlite3'
    conn = sqlite3.connect(path)
    legacy = SCHEMA.split('CREATE TABLE IF NOT EXISTS authors')[0]
    conn.executescript(legacy)
    conn.execute("INSERT INTO users(name,email,password_hash,role,is_locked,session_version) VALUES('Old','old@example.com','existing-hash','Admin',1,8)")
    conn.commit()
    before = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only', 'DATABASE': str(path)})
    for _ in range(2):
        result = app.test_cli_runner().invoke(args=['upgrade-db'])
        assert result.exit_code == 0, result.output
    conn = sqlite3.connect(path)
    assert conn.execute('SELECT * FROM users').fetchall() == before
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    conn.close()


def test_database_constraints(seeded):
    with seeded.app_context():
        db = get_db()
        for field, value in [('stock', -1), ('stock', 1.5), ('price_cents', 0), ('price_cents', 1.5), ('author_id', 999999)]:
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(f'UPDATE books SET {field}=? WHERE id=1', (value,))
            db.rollback()


@pytest.mark.parametrize('kind,column', [('authors', 'author_id'), ('genres', 'genre_id')])
def test_metadata_delete_blocked_when_linked(seeded, client, kind, column):
    login(client)
    used = rows(seeded, f'SELECT {column} AS id FROM books ORDER BY id LIMIT 1')[0]['id']
    response = post(client, f'/admin/metadata/{kind}/{used}/delete', {}, follow_redirects=True)
    assert 'Cannot delete' in response.text
    assert len(rows(seeded, f'SELECT * FROM {kind} WHERE id=?', (used,))) == 1
    post(client, f'/admin/metadata/{kind}', {'name': 'Unused Entry'})
    unused = rows(seeded, f"SELECT * FROM {kind} WHERE name='Unused Entry'")[0]['id']
    assert post(client, f'/admin/metadata/{kind}/{unused}/delete', {}).status_code == 302
    assert rows(seeded, f'SELECT * FROM {kind} WHERE id=?', (unused,)) == []
    assert post(client, f'/admin/metadata/{kind}/999999/delete', {}).status_code == 404


def test_metadata_delete_requires_admin(seeded, client):
    assert post(client, '/admin/metadata/genres/1/delete', {}).status_code in (302, 401, 403)
    login(client, 'reader@example.com')
    assert post(client, '/admin/metadata/genres/1/delete', {}).status_code == 403
    assert post(client, '/admin/metadata/users/1/delete', {}).status_code in (403, 404)
