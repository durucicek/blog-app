import os
import tempfile

import pytest
from flaskr import create_app
from flaskr.database import get_db, init_db

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()

class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post(
            '/auth/login',
            data={'username': username, 'password': password}
        )

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)


class BlogActions(object):
    def __init__(self, client):
        self._client = client

    def create(self, title='test', body='test body'):
        return self._client.post(
            '/create',
            data={'title': title, 'body': body}
        )
    
    def update(self, id=1, title='updated', body='updated body'):
        return self._client.post(
            f'/{id}/update',  
            data={'title': title, 'body': body}
        )
    
    def delete(self, id=1):
        return self._client.post(
            f'/{id}/delete'  
        )
    
    def like(self, postid=1, userid=1):
        return self._client.post(
            f'/{userid}/{postid}/like', 
        )
    
@pytest.fixture
def blog(client):
    return BlogActions(client)