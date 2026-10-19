import pytest
from app import app
from models import db, User, Note

@pytest.fixture
def client():
    # Configure app for testing with an in-memory SQLite database
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()

            # Create a test user for test setup
            user1 = User(username='test_user1')
            user1.password_hash = 'password123'

            user2 = User(username='test_user2')
            user2.password_hash = 'password123'

            db.session.add_all([user1, user2])
            db.session.commit()

            # Add test notes for user1
            for i in range(12):
                note = Note(
                    title=f'User1 Note {i+1}',
                    content=f'Content for note {i+1}',
                    category='Work',
                    user_id=user1.id
                )
                db.session.add(note)

            # Add one note for user2
            user2_note = Note(
                title='User2 Private Note',
                content='Top secret content',
                category='Personal',
                user_id=user2.id
            )
            db.session.add(user2_note)
            db.session.commit()

        yield client

        with app.app_context():
            db.drop_all()


# --- Auth Tests ---

def test_signup_success(client):
    res = client.post('/signup', json={
        'username': 'newuser',
        'password': 'mypassword'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['username'] == 'newuser'
    assert 'id' in data

    # Verify session is created
    session_res = client.get('/check_session')
    assert session_res.status_code == 200
    assert session_res.get_json()['username'] == 'newuser'


def test_signup_duplicate_username(client):
    res = client.post('/signup', json={
        'username': 'test_user1',
        'password': 'password123'
    })
    assert res.status_code == 409
    assert 'Username already taken' in res.get_json()['error']


def test_signup_validation_errors(client):
    # Missing username
    res = client.post('/signup', json={'password': 'password123'})
    assert res.status_code == 400

    # Short password
    res = client.post('/signup', json={'username': 'bob', 'password': '12'})
    assert res.status_code == 400


def test_login_success_and_logout(client):
    login_res = client.post('/login', json={
        'username': 'test_user1',
        'password': 'password123'
    })
    assert login_res.status_code == 200
    assert login_res.get_json()['username'] == 'test_user1'

    # Check session
    chk = client.get('/check_session')
    assert chk.status_code == 200

    # Logout
    logout_res = client.delete('/logout')
    assert logout_res.status_code == 200

    # Check session after logout
    chk_after = client.get('/check_session')
    assert chk_after.status_code == 401


def test_login_invalid_credentials(client):
    res = client.post('/login', json={
        'username': 'test_user1',
        'password': 'wrongpassword'
    })
    assert res.status_code == 401


def test_check_session_unauthorized(client):
    res = client.get('/check_session')
    assert res.status_code == 401


# --- Note CRUD & Pagination Tests ---

def test_notes_pagination_and_ownership(client):
    # Log in as test_user1
    client.post('/login', json={'username': 'test_user1', 'password': 'password123'})

    # Request page 1 with 5 items per page
    res = client.get('/notes?page=1&per_page=5')
    assert res.status_code == 200
    data = res.get_json()

    assert 'notes' in data
    assert len(data['notes']) == 5
    assert data['total'] == 12
    assert data['page'] == 1
    assert data['per_page'] == 5
    assert data['pages'] == 3

    # Ensure all returned notes belong to user1
    for note in data['notes']:
        assert 'User1 Note' in note['title']


def test_create_note(client):
    client.post('/login', json={'username': 'test_user1', 'password': 'password123'})

    res = client.post('/notes', json={
        'title': 'Sprint Review Prep',
        'content': 'Prepare slide deck for demo',
        'category': 'Work'
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data['title'] == 'Sprint Review Prep'
    assert data['category'] == 'Work'
    assert 'id' in data


def test_create_note_validation(client):
    client.post('/login', json={'username': 'test_user1', 'password': 'password123'})

    # Missing title
    res = client.post('/notes', json={'content': 'No title here'})
    assert res.status_code == 400

    # Missing content
    res = client.post('/notes', json={'title': 'No content'})
    assert res.status_code == 400


def test_update_note(client):
    client.post('/login', json={'username': 'test_user1', 'password': 'password123'})

    # Update note with id 1
    res = client.patch('/notes/1', json={
        'title': 'Updated Title',
        'content': 'Updated content body'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['title'] == 'Updated Title'
    assert data['content'] == 'Updated content body'


def test_delete_note(client):
    client.post('/login', json={'username': 'test_user1', 'password': 'password123'})

    # Delete note with id 1
    del_res = client.delete('/notes/1')
    assert del_res.status_code == 200

    # Getting note 1 should now return 404
    get_res = client.get('/notes/1')
    assert get_res.status_code == 404


# --- Security & Cross-User Isolation Tests ---

def test_unauthenticated_cannot_access_notes(client):
    # Without logging in
    assert client.get('/notes').status_code == 401
    assert client.post('/notes', json={'title': 'A', 'content': 'B'}).status_code == 401
    assert client.get('/notes/1').status_code == 401
    assert client.patch('/notes/1', json={'title': 'A'}).status_code == 401
    assert client.delete('/notes/1').status_code == 401


def test_user_cannot_access_or_modify_other_users_note(client):
    # Log in as test_user1
    client.post('/login', json={'username': 'test_user1', 'password': 'password123'})

    # Note 13 belongs to test_user2
    # User 1 should get 404 when trying to view, edit, or delete it
    assert client.get('/notes/13').status_code == 404
    assert client.patch('/notes/13', json={'title': 'Hacked Title'}).status_code == 404
    assert client.delete('/notes/13').status_code == 404
