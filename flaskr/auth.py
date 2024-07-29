import functools
from flaskr.database import db, jwt
from sqlalchemy import select
from datetime import timedelta

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for, make_response
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.models import User
from flask_jwt_extended import create_access_token, jwt_required, current_user, JWTManager

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Register a callback function that takes whatever object is passed in as the
# identity when creating JWTs and converts it to a JSON serializable format.
@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id


# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    print(jwt_data)
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()

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
            access_token = create_access_token(identity=user, expires_delta=timedelta(hours=1))
            response = make_response(redirect(url_for('index')))
            # Set the JWT token as a cookie
            response.set_cookie('access_token_cookie', access_token, httponly=True)
            return response

        flash(error)

    return render_template('auth/login.html')
@bp.route('/logout')
@jwt_required()
def logout():
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie('access_token', '', expires=0)  # Clear the cookie
    return response

# def login_required(view):
#     @functools.wraps(view)
#     def wrapped_view(**kwargs):
#         if not current_user:
#             flash('You must be logged in to view this page.', 'error')
#             return redirect(url_for('auth.login')), 403
#         return view(**kwargs)
#     return wrapped_view


