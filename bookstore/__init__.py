import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

csrf = CSRFProtect()


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY'),
        DATABASE=os.environ.get('DATABASE') or str(Path(app.instance_path) / 'bookstore.sqlite3'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE', '').lower() == 'true',
        MAX_CONTENT_LENGTH=64 * 1024,
    )
    if test_config:
        app.config.update(test_config)
    if not app.config['SECRET_KEY']:
        raise RuntimeError('Set SECRET_KEY in your environment or .env file. See README.md.')
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    from . import db, auth, admin
    db.init_app(app)
    csrf.init_app(app)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return render_template('error.html', title='Form expired', message='This form is missing a valid security token. Reload the page and try again.'), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('error.html', title='Access denied', message='You do not have permission to open this page.'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', title='Page not found', message='We could not find this page.'), 404

    return app
