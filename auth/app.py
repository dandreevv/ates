import os
from flask import Flask
from .models import db
from .oauth2 import config_oauth
from .routes import bp

os.environ.setdefault('AUTHLIB_INSECURE_TRANSPORT', '1')

def create_app(config=None):
    app = Flask(__name__)

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)
    # app.config.update(
    #     {
    #         "SESSION_COOKIE_SAMESITE": "Lax"
    #     }
    # )
    setup_app(app)
    return app


def setup_app(app):

    db.init_app(app)
    # Create tables if they do not exist already
    with app.app_context():
        db.create_all()
    config_oauth(app)

    app.register_blueprint(bp, url_prefix='')


app = create_app(
    {
        'SECRET_KEY': 'secret',
        'OAUTH2_REFRESH_TOKEN_GENERATOR': True,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SQLALCHEMY_DATABASE_URI': os.environ['DB_URL'],
        'KAFKA_BOOTSTRAP_SERVERS': os.environ['KAFKA_BOOTSTRAP_SERVERS'],
    }
)

