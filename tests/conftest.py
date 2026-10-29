import re

import pytest
from werkzeug.security import generate_password_hash

from bookstore import create_app
from bookstore.db import SCHEMA, get_db

PASSWORD = 'a-long-test-password'


@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only-secret', 'DATABASE': str(tmp_path / 'test.sqlite3')})
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        for name, email, role in [('Admin One', 'admin@example.com', 'Admin'), ('Reader One', 'reader@example.com', 'Customer')]:
            db.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)',
                       (name, email, generate_password_hash(PASSWORD), role))
        db.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, url, data=None, page='/login', **kwargs):
    response = client.get(page)
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)
    return client.post(url, data={**(data or {}), 'csrf_token': token}, **kwargs)


def login(client, email='admin@example.com'):
    return post(client, '/login', {'email': email, 'password': PASSWORD})
