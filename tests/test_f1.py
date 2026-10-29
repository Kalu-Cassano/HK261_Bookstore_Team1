import pytest
from werkzeug.security import check_password_hash

from bookstore.db import get_db
from conftest import PASSWORD, login, post


def row(app, email):
    with app.app_context():
        return get_db().execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()


def registration(**overrides):
    return dict(name='New Reader', email='new@example.com', password=PASSWORD, confirm_password=PASSWORD, **overrides)


def test_registration_is_customer_and_password_is_hashed(client, app):
    response = post(client, '/register', {**registration(), 'role': 'Admin', 'is_locked': '0'})
    assert response.status_code == 302
    user = row(app, 'new@example.com')
    assert user['role'] == 'Customer'
    assert user['password_hash'] != PASSWORD
    assert check_password_hash(user['password_hash'], PASSWORD)


@pytest.mark.parametrize('field,value,message', [
    ('name', 'x', 'Name must'), ('name', ' ' * 3, 'Name must'),
    ('email', 'bad-email', 'valid email'), ('email', 'x' * 255, 'valid email'),
    ('password', 'short', 'Password must'), ('password', 'x' * 129, 'Password must'),
    ('confirm_password', 'wrong-password', 'Passwords do not match'),
])
def test_registration_validation(client, app, field, value, message):
    response = post(client, '/register', {**registration(), field: value})
    assert response.status_code == 400
    assert message in response.text
    assert row(app, 'new@example.com') is None


def test_duplicate_email_case_insensitive(client):
    response = post(client, '/register', {**registration(), 'email': ' READER@EXAMPLE.COM '})
    assert response.status_code == 400
    assert 'already in use' in response.text


def test_login_logout_and_protected_page(client):
    assert client.get('/account').status_code == 302
    assert login(client, 'reader@example.com').status_code == 302
    assert 'Hello, Reader One.' in client.get('/account').text
    assert client.get('/logout').status_code == 405
    assert post(client, '/logout', page='/account').status_code == 302
    assert client.get('/account').status_code == 302


@pytest.mark.parametrize('email,password', [('reader@example.com', 'incorrect-password'), ('missing@example.com', PASSWORD), ('reader@example.com', '')])
def test_invalid_login(client, email, password):
    assert post(client, '/login', {'email': email, 'password': password}).status_code == 400
    assert client.get('/account').status_code == 302


@pytest.mark.parametrize('url', ['/admin/accounts', '/admin/accounts/new'])
def test_admin_pages_reject_anonymous_and_customer(client, url):
    assert client.get(url).status_code == 302
    login(client, 'reader@example.com')
    assert client.get(url).status_code == 403


def test_customer_cannot_mutate_admin_accounts(client, app):
    login(client, 'reader@example.com')
    assert post(client, '/admin/accounts/new', registration(), page='/account').status_code == 403
    assert post(client, '/admin/accounts/1/update', {'role': 'Customer', 'state': 'locked'}, page='/account').status_code == 403
    assert row(app, 'admin@example.com')['role'] == 'Admin'
    assert row(app, 'new@example.com') is None


def test_anonymous_cannot_mutate_admin_accounts(client, app):
    assert post(client, '/admin/accounts/new', {**registration(), 'role': 'Admin'}).status_code == 302
    assert post(client, '/admin/accounts/1/update', {'role': 'Customer', 'state': 'locked'}).status_code == 302
    assert row(app, 'new@example.com') is None
    assert row(app, 'admin@example.com')['is_locked'] == 0


@pytest.mark.parametrize('role', ['Admin', 'Customer'])
def test_admin_list_and_create(client, app, role):
    login(client)
    response = client.get('/admin/accounts')
    assert response.status_code == 200 and 'reader@example.com' in response.text
    assert post(client, '/admin/accounts/new', {**registration(), 'role': role}).status_code == 302
    assert row(app, 'new@example.com')['role'] == role


def test_admin_create_validation(client, app):
    login(client)
    assert post(client, '/admin/accounts/new', {**registration(), 'role': 'Owner'}).status_code == 400
    assert row(app, 'new@example.com') is None
    assert post(client, '/admin/accounts/new', {**registration(), 'role': 'Customer', 'email': 'reader@example.com'}).status_code == 400


@pytest.mark.parametrize('role,state', [('Admin', 'locked'), ('Customer', 'active'), ('Customer', 'locked')])
def test_last_active_admin_is_kept(client, app, role, state):
    login(client)
    response = post(client, '/admin/accounts/1/update', {'role': role, 'state': state}, follow_redirects=True)
    assert 'Keep at least one active Admin' in response.text
    user = row(app, 'admin@example.com')
    assert user['role'] == 'Admin' and user['is_locked'] == 0


def test_lock_ends_session_unlock_requires_new_login(client, app):
    reader = app.test_client()
    login(reader, 'reader@example.com')
    login(client)
    assert post(client, '/admin/accounts/2/update', {'role': 'Customer', 'state': 'locked'}).status_code == 302
    assert reader.get('/account').status_code == 302
    assert login(reader, 'reader@example.com').status_code == 400
    post(client, '/admin/accounts/2/update', {'role': 'Customer', 'state': 'active'})
    assert reader.get('/account').status_code == 302
    assert login(reader, 'reader@example.com').status_code == 302


def test_unvisited_old_session_stays_invalid_after_unlock(client, app):
    reader = app.test_client()
    login(reader, 'reader@example.com')
    login(client)
    post(client, '/admin/accounts/2/update', {'role': 'Customer', 'state': 'locked'})
    post(client, '/admin/accounts/2/update', {'role': 'Customer', 'state': 'active'})
    assert reader.get('/account').status_code == 302


def test_demotion_takes_effect_in_existing_admin_session(client, app):
    login(client)
    post(client, '/admin/accounts/new', {**registration(), 'role': 'Admin'})
    other_admin = app.test_client()
    login(other_admin, 'new@example.com')
    post(client, '/admin/accounts/3/update', {'role': 'Customer', 'state': 'active'})
    assert other_admin.get('/admin/accounts').status_code == 403


def test_locked_admin_session_denied_and_locked_admin_not_counted(client, app):
    login(client)
    post(client, '/admin/accounts/new', {**registration(), 'role': 'Admin'})
    other = app.test_client()
    login(other, 'new@example.com')
    post(client, '/admin/accounts/3/update', {'role': 'Admin', 'state': 'locked'})
    assert other.get('/admin/accounts').status_code == 302
    assert post(other, '/admin/accounts/2/update', {'role': 'Admin', 'state': 'active'}).status_code == 302
    post(client, '/admin/accounts/1/update', {'role': 'Customer', 'state': 'active'})
    assert row(app, 'admin@example.com')['role'] == 'Admin'


@pytest.mark.parametrize('url', ['/register', '/login', '/logout', '/admin/accounts/new', '/admin/accounts/2/update'])
@pytest.mark.parametrize('token', [None, 'bad-token'])
def test_csrf_required_for_all_mutations(client, app, url, token):
    login(client)
    data = registration()
    if token:
        data['csrf_token'] = token
    response = client.post(url, data=data)
    assert response.status_code == 400
    assert 'security token' in response.text
    assert row(app, 'new@example.com') is None
    assert row(app, 'reader@example.com')['is_locked'] == 0


def test_invalid_admin_update_and_missing_target(client):
    login(client)
    assert post(client, '/admin/accounts/2/update', {'role': 'Owner', 'state': 'active'}).status_code == 400
    assert post(client, '/admin/accounts/2/update', {'role': 'Admin', 'state': 'unknown'}).status_code == 400
    assert post(client, '/admin/accounts/999/update', {'role': 'Customer', 'state': 'active'}).status_code == 404
    assert client.get('/admin/accounts/2/update').status_code == 405


def test_cli_init_preserves_accounts_and_create_admin(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=['init-db']).exit_code == 0
    assert row(app, 'reader@example.com') is not None
    result = runner.invoke(args=['create-admin', '--name', 'CLI Admin', '--email', 'cli@example.com'], input=f'{PASSWORD}\n{PASSWORD}\n')
    assert result.exit_code == 0, result.output
    assert row(app, 'cli@example.com')['role'] == 'Admin'
    assert check_password_hash(row(app, 'cli@example.com')['password_hash'], PASSWORD)
    assert runner.invoke(args=['create-admin', '--name', 'CLI Admin', '--email', 'cli@example.com'], input=f'{PASSWORD}\n{PASSWORD}\n').exit_code != 0
    assert runner.invoke(args=['create-admin', '--name', 'CLI Admin', '--email', 'bad-email'], input=f'{PASSWORD}\n{PASSWORD}\n').exit_code != 0


def test_templates_escape_names(client):
    post(client, '/register', {**registration(), 'name': '<script>alert(1)</script>'})
    login(client, 'new@example.com')
    response = client.get('/account')
    assert '<script>alert(1)</script>' not in response.text
    assert '&lt;script&gt;' in response.text
