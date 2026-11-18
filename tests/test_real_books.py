import pytest

from bookstore.db import get_db
from bookstore.real_books import REAL_BOOKS
from conftest import login


def seed(app, command):
    result = app.test_cli_runner().invoke(args=[command])
    assert result.exit_code == 0, result.output
    return result.output


def snapshot(app):
    with app.app_context():
        return {table: [tuple(row) for row in get_db().execute(f'SELECT * FROM {table} ORDER BY id')]
                for table in ('users', 'books', 'authors', 'genres')}


@pytest.mark.parametrize('stored,expected', [
    (23000000, '230.000 ₫'), (46455000, '464.550 ₫'),
    (12500050, '125.000,50 ₫'), (1, '0,01 ₫'), (0, '0 ₫'),
    (99999999999, '999.999.999,99 ₫'),
])
def test_money_exact_without_float_rounding(app, stored, expected):
    assert app.jinja_env.filters['money'](stored) == expected


def test_real_seed_adds_16_once_and_preserves_demo_and_accounts(app):
    seed(app, 'seed-books')
    before = snapshot(app)
    assert 'Inserted 16 real books. Total books: 52' in seed(app, 'seed-real-books')
    after = snapshot(app)
    assert after['users'] == before['users']
    assert after['books'][:36] == before['books']
    with app.app_context():
        db = get_db()
        for slug, title, author, genre, price, description in REAL_BOOKS:
            row = db.execute('''SELECT b.*, a.name AS author, g.name AS genre FROM books b
                JOIN authors a ON a.id=b.author_id JOIN genres g ON g.id=b.genre_id
                WHERE b.demo_key=?''', ('real-books-v1-' + slug,)).fetchone()
            assert (row['title'], row['author'], row['genre'], row['price_cents'], row['description']) == (title, author, genre, price*100, description)
            assert row['stock'] == 10 and row['cover_url'] == ''
        assert db.execute("SELECT COUNT(*) FROM authors WHERE name='Michele Cagan'").fetchone()[0] == 1
    assert 'Inserted 0 real books. Total books: 52' in seed(app, 'seed-real-books')
    assert snapshot(app) == after


def test_real_seed_does_not_overwrite_edited_or_hidden_real_book(app):
    seed(app, 'seed-real-books')
    with app.app_context():
        db = get_db()
        db.execute("UPDATE books SET title='My edited title', price_cents=123456, stock=0, is_hidden=1, description='Edited' WHERE id=1")
        db.commit()
    before = snapshot(app)
    assert 'Inserted 0 real books' in seed(app, 'seed-real-books')
    assert snapshot(app) == before


def test_real_seed_reuses_metadata_and_skips_manual_book(app):
    with app.app_context():
        db = get_db()
        aid = db.execute("INSERT INTO authors(name) VALUES('michele cagan')").lastrowid
        gid = db.execute("INSERT INTO genres(name) VALUES('personal finance')").lastrowid
        db.execute('''INSERT INTO books(title,author_id,genre_id,price_cents,description,stock,is_hidden,isbn)
            VALUES('debt 101',?,?,99900,'Keep my changes',4,1,'9780000000001')''', (aid,gid))
        db.commit()
        original = tuple(db.execute('SELECT * FROM books WHERE id=1').fetchone())
    assert 'Inserted 15 real books. Total books: 16' in seed(app, 'seed-real-books')
    with app.app_context():
        db = get_db()
        assert tuple(db.execute('SELECT * FROM books WHERE id=1').fetchone()) == original
        assert db.execute("SELECT COUNT(*) FROM authors WHERE casefold(name)='michele cagan'").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM genres WHERE casefold(name)='personal finance'").fetchone()[0] == 1
        assert db.execute("SELECT author_id FROM books WHERE title='Real Estate Investing 101'").fetchone()[0] == aid
    before = snapshot(app)
    assert 'Inserted 0 real books' in seed(app, 'seed-real-books')
    assert snapshot(app) == before


def test_real_book_prices_on_list_detail_admin_and_numeric_filter(app, client):
    seed(app, 'seed-books')
    seed(app, 'seed-real-books')
    with app.app_context():
        db = get_db()
        bitcoin = db.execute("SELECT id FROM books WHERE title='Bitcoin Is for Everyone'").fetchone()[0]
        demo = db.execute('SELECT id FROM books WHERE price_cents=23000000').fetchone()[0]
    for title, price, book_id in [('Bitcoin Is for Everyone','464.550 ₫',bitcoin), ('Bookstore Demo 36','230.000 ₫',demo)]:
        listing = client.get('/books', query_string={'q': title})
        assert listing.status_code == 200 and price in listing.text
        detail = client.get(f'/books/{book_id}')
        assert detail.status_code == 200 and price in detail.text
        assert '230,000.00 VND' not in listing.text + detail.text
    response = client.get('/books?q=Bitcoin&min_price=464550&max_price=464550')
    assert response.status_code == 200 and '464.550 ₫' in response.text
    assert 'value="464550"' in response.text
    assert 'No books found' in client.get('/books?q=Bitcoin&max_price=464549').text
    assert 'No books found' in client.get('/books?q=Bitcoin&min_price=464551').text
    assert 'Michele Cagan' in client.get('/books?q=Michele%20Cagan').text
    login(client)
    admin = client.get('/admin/books')
    assert admin.status_code == 200 and '464.550 ₫' in admin.text and '230.000 ₫' in admin.text
    edit = client.get(f'/admin/books/{bitcoin}/edit')
    assert 'value="464550.00"' in edit.text
    assert 'value="464.550 ₫"' not in edit.text
