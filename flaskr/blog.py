from flask import (
    Blueprint, flash, jsonify, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flaskr.models import User, Post, LikedPosts, Tags
from flaskr.database import db
from flask_jwt_extended import current_user, jwt_required


bp = Blueprint('blog', __name__)

@bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # This will work if the JWT cookie is present
    return jsonify(message="You have access to this protected route.")

@bp.route('/')
@jwt_required()
def index():
    stmt = db.select(Post).order_by(Post.created.desc())
    posts = db.session.execute(stmt).scalars().all()
    liked_posts_ids = []
    print(current_user)
    user_id = current_user.id if current_user else None
    username = current_user.username if current_user else None
    if user_id:
        user = User.query.get(user_id)
        if not user:
            return render_template('error.html', message="User not found"), 404
        liked_posts_ids = [liked.post_id for liked in user.liked_posts]
    return render_template('blog/index.html', posts=posts, liked_posts=liked_posts_ids, 
                           id=user_id, username=username)

@bp.route('/create', methods=('GET', 'POST'))
#@login_required
@jwt_required()
def create():
    tags = db.session.execute(db.select(Tags)).scalars().all()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        selected_tags = request.form.getlist('tags')
        error = None
        if not title:
            error = 'Title is required.'
        if error is not None:
            flash(error)
        else:
            post = Post(title=title, body=body, author_id=current_user.id)
            for tag_id in selected_tags:
                tag = Tags.query.get(tag_id)
                if tag:
                    post.tags.append(tag)
            db.session.add(post)
            db.session.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/create.html', tags=tags)

def get_post(id, check_author=True):
    stmt = db.select(Post).join(User, Post.author_id == User.id).where(Post.id == id)
    post = db.session.execute(stmt).scalar()
    if post is None:
        abort(404, f"Post id {id} doesn't exist.")
    if check_author and post.author_id != current_user.id:
        flash("You don't have permission to update this post.")
    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
#@login_required
@jwt_required()
def update(id):
    post = get_post(id)
    tags = db.session.execute(db.select(Tags)).scalars().all()

    if request.method == 'GET':
        selected_tags = [tag.id for tag in post.tags]
    else:
        selected_tags = request.form.getlist('tags')

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
            stmt = db.select(Tags).where(Tags.id.in_(selected_tags))
            post.tags = db.session.execute(stmt).scalars().all()
            db.session.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post, tags=tags, selected_tags=selected_tags)

@bp.route('/<int:id>/delete', methods=('POST',))
#@login_required
@jwt_required()
def delete(id):
    post = get_post(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<postid>/like', methods=['POST'])
#@login_required
@jwt_required()
def like(postid):
    try:
        postid = int(postid)
    except ValueError:
        return jsonify({'error': 'Post ID must be integers'}), 400
    user = current_user
    post = Post.query.get(postid)
    if user is None:
        return jsonify({'error': "User doesn't exist"}), 404
    if post is None:
        return jsonify({'error': "Post doesn't exist"}), 404
    
    userid = user.id
    stmt = db.select(LikedPosts).where(LikedPosts.user_id == userid, LikedPosts.post_id == postid)
    liked_post = db.session.execute(stmt).scalar()
    if liked_post is None:
        post.likes += 1
        new_like = LikedPosts(user_id=userid, post_id=postid)
        db.session.add(new_like)
    else:
        post.likes -= 1
        db.session.delete(liked_post)

    db.session.commit()
    return redirect(url_for('blog.index'))

@bp.route('/add-tag', methods=['POST'])
#@login_required
@jwt_required()
def add_tag():
    tag_name = request.json.get('tag_name')
    if not tag_name:
        return jsonify({'success': False, 'error': 'Tag name is required'}), 400

    stmt = db.select(Tags).where(Tags.name == tag_name)
    existing_tag = db.session.execute(stmt).scalar()

    if existing_tag:
        return jsonify({'success': False, 'error': 'Tag already exists'}), 409

    new_tag = Tags(name=tag_name)
    db.session.add(new_tag)
    db.session.commit()

    return jsonify({'success': True, 'tagId': new_tag.id, 'tagName': new_tag.name}), 201

@bp.route('/tags', methods=['GET'])
def get_tags():
    tags = db.session.execute(db.select(Tags)).scalars().all()
    return render_template('blog/tag.html', tags=tags)
