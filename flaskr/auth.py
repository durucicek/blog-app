from flaskr.database import db, jwt
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
import requests

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, make_response, jsonify
)
from flask import request
from flask_jwt_extended import (
    get_jwt, set_access_cookies, unset_jwt_cookies, jwt_required, create_access_token, jwt_required, get_jwt, current_user, create_refresh_token
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

###########################################
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    print(jwt_data)
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()
###########################################
@jwt.expired_token_loader
def expired_token_callback(jwt_header, error):
    return redirect(url_for('auth.login'))

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return redirect(url_for('auth.login'))

@jwt.unauthorized_loader
def missing_token_callback(error):
    return redirect(url_for('auth.login'))
###########################################

@bp.after_app_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now(timezone.utc)
        target_timestamp = datetime.timestamp(now + timedelta(hours=1))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=current_user, expires_delta=timedelta(minutes=10))
            set_access_cookies(response, access_token)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original response
        return response

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        if error is None:
            try:
                new_user = User(username=username, password=generate_password_hash(password))
                db.session.add(new_user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                error = f"User {username} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        stmt = select(User).where(User.username == username)
        user = db.session.execute(stmt).scalar()
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            access_token = create_access_token(identity=user, expires_delta=timedelta(seconds=10))
            response = make_response(redirect(url_for('index')))
            response.set_cookie('access_token_cookie', access_token, httponly=True)
            return response
        flash(error)

    return render_template('auth/login.html')

@bp.route('/logout')
@jwt_required()
def logout():
    response = make_response(redirect(url_for('auth.login')))
    unset_jwt_cookies(response)
    return response

# def login_required(view):
#     @functools.wraps(view)
#     def wrapped_view(**kwargs):
#         if not current_user:
#             flash('You must be logged in to view this page.', 'error')
#             return redirect(url_for('auth.login')), 403
#         return view(**kwargs)
#     return wrapped_view


