import pytest
from flaskr.database import get_db

@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"


def test_author_required(app, client, auth):
    # change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify other user's post
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    # current user doesn't see edit link
    assert b'href="/1/update"' not in client.get('/').data


@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    client.post('/create', data={'title': 'created', 'body': ''})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2


def test_update(client, auth, app):
    auth.login()
    assert client.get('/1/update').status_code == 200
    client.post('/1/update', data={'title': 'updated', 'body': ''})

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'


@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required.' in response.data

def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None


def test_like(client, auth, app):
    auth.login()
    response = client.post('/1/1/like')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        likes = db.execute('SELECT likes FROM post WHERE id = 1').fetchone()[0]
        assert likes == 11
        assert db.execute('SELECT * FROM liked_posts WHERE post_id = 1 AND user_id = 1').fetchone() is not None


@pytest.mark.parametrize('path', (
    '/1/1/like',
    '/1/1/like'
))
def test_like_unlike_post(client, auth, blog, path, app):
    auth.login()
    response = client.post(path)
    assert response.status_code == 302  # Check redirection after like/unlike

    with app.app_context():
        db = get_db()
        likes = db.execute('SELECT likes FROM post WHERE id = 1').fetchone()[0]
        if path == '/1/1/like':
            assert likes == 11
        else:
            assert likes == 10

        if likes == 11:
            assert db.execute('SELECT * FROM liked_posts WHERE post_id = 1 AND user_id = 1').fetchone() is not None
        else:
            assert db.execute('SELECT * FROM liked_posts WHERE post_id = 1 AND user_id = 1').fetchone() is None


def test_like_button_text(client, auth):
    auth.login()
    response = client.get('/')
    assert b'Like' in response.data

    client.post('/1/1/like')
    response = client.get('/')
    assert b'Unlike' in response.data

    client.post('/1/1/like')
    response = client.get('/')
    assert b'Like' in response.data


def full_test(client, auth, app):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'username': 'test', 'password': '123'}
    )
    assert response.headers["Location"] == "/auth/login"
    with app.app_context():
            assert get_db().execute(
                "SELECT * FROM user WHERE username = 'a'",
            ).fetchone() is not None

    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers["Location"] == "/"

    assert client.get('/').status_code == 200
    assert client.get('/create').status_code == 200

    client.post('/create', data={'title': 'created', 'body': 'this is a test'})
    assert client.get('/').status_code == 200
    assert b'created' in client.get('/').data

    client.post('/1/update', data={'title': 'updated', 'body': 'this is a test'})
    assert client.get('/').status_code == 200
    assert b'updated' in client.get('/').data

    response = client.post('/1/delete')
    assert response.headers["Location"] == "/"
    assert client.get('/').status_code == 200
    assert b'created' not in client.get('/').data

    client.post('/create', data={'title': 'created', 'body': 'this is a test'})
    response = client.post('/1/1/like')
    assert response.headers["Location"] == "/"
    assert client.get('/').status_code == 200
    assert b'Like' in client.get('/').data

    response = client.post('/1/1/like')
    assert response.headers["Location"] == "/"
    assert client.get('/').status_code == 200
    assert b'Unlike' in client.get('/').data

    
def test_blog_operations(auth, blog, app):
    auth.login()

    blog.create(title="Title", body="Body")
    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2


    blog.update(id=2, title="UpdatedTitle", body="Updated Body")
    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 2').fetchone()
        assert post['title'] == "UpdatedTitle"

    blog.delete(id=2)
    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 2').fetchone()
        assert post is None

    blog.like(postid=1, userid=1)
    with app.app_context():
        db = get_db()
        likes = db.execute('SELECT likes FROM post WHERE id = 1').fetchone()[0]
        assert likes == 11
        assert db.execute('SELECT * FROM liked_posts WHERE post_id = 1 AND user_id = 1').fetchone() is not None

    blog.like(postid=1, userid=1)
    with app.app_context():
        db = get_db()
        likes = db.execute('SELECT likes FROM post WHERE id = 1').fetchone()[0]
        assert likes == 10
        assert db.execute('SELECT * FROM liked_posts WHERE post_id = 1 AND user_id = 1').fetchone() is None

       
        
@pytest.mark.parametrize('userid, postid, is_logged_in, status_code', (
    [1,1,1, 302],
    [1,1,0, 403],
    [50,1,1, 404],
    [1,50,1, 404],    
    [50,50,1, 404],
    ["test","test",1, 400],
    ["test",1,1, 400],
    [1,"test",1, 400],
    [50,50,0, 403],
))

def test_parameterized(auth, blog, userid, postid, is_logged_in, status_code):
    if is_logged_in == 1:
        auth.login()

    response = blog.create(title="Title", body="Body")
    if is_logged_in == 0:
        assert response.headers["Location"] == "/auth/login"
    response = blog.like(userid, postid)
    assert response.status_code == status_code
