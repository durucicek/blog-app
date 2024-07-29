from flask import Flask
from .config import config
from flaskr import database
from flaskr.models import User, Post

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


def create_app(config_mode='development'):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config[config_mode])
    database.init_app(app)

    jwt = JWTManager(app)

    from . import auth
    app.register_blueprint(auth.bp)
    from . import blog
    app.register_blueprint(blog.bp)

    app.add_url_rule('/', endpoint='index')

    return app, jwt
