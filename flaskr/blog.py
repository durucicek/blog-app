from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.models import User, Post, LikedPosts
from flaskr.database import db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    user_id = g.get('id')
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return render_template('error.html', message="User not found"), 404
        posts = user.posts  
        liked_posts_ids = [liked.post_id for liked in user.liked_posts]
    else:
        posts = Post.query.order_by(Post.created.desc()).all()
        liked_posts_ids = []

    return render_template('blog/index.html', posts=posts, liked_posts=liked_posts_ids)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            post = Post(title=title, body=body, author_id=g.user.id)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    stmt = db.select(Post).join(User, Post.author_id == User.id).where(Post.id == id)
    post = db.session.execute(stmt).scalar()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post.author_id != g.user.id:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
            db.session.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<userid>/<postid>/like', methods=['POST'])
@login_required
def like(userid, postid):
    try:
        userid = int(userid)
        postid = int(postid)
    except ValueError:
        return jsonify({'error': 'User ID and Post ID must be integers'}), 400
    
    user = User.query.get(userid)
    post = Post.query.get(postid)
    
    if user is None:
        return jsonify({'error': "User doesn't exist"}), 404
    if post is None:
        return jsonify({'error': "Post doesn't exist"}), 404
    
    liked_post = LikedPosts.query.filter_by(user_id=userid, post_id=postid).first()

    if liked_post is None:
        post.likes += 1
        new_like = LikedPosts(user_id=userid, post_id=postid)
        
        db.session.add(new_like)
    else:
        post.likes -= 1
        db.session.delete(liked_post)
    
    db.session.commit()
    return redirect(url_for('blog.index'))
