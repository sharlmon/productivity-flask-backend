import os
from flask import Flask, request, session, jsonify
from flask_restful import Api, Resource
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, bcrypt, User, Note

# App initialization
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-dev-key-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

# Enable CORS for frontend client app integration with cookies
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"])

db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
api = Api(app)


# --- Helper function for auth check ---
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.filter_by(id=user_id).first()


# --- Authentication Endpoints ---

class Signup(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Basic validations
        if not username or not password:
            return {'error': 'Username and password are required'}, 400

        if len(username) < 3:
            return {'error': 'Username must be at least 3 characters long'}, 400

        if len(password) < 4:
            return {'error': 'Password must be at least 4 characters long'}, 400

        if User.query.filter_by(username=username).first():
            return {'error': 'Username already taken'}, 409

        try:
            new_user = User(username=username)
            new_user.password_hash = password
            db.session.add(new_user)
            db.session.commit()

            # Log user in upon registration
            session['user_id'] = new_user.id
            return new_user.to_dict(), 201
        except ValueError as ve:
            return {'error': str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': 'Could not create user'}, 500


class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return {'error': 'Username and password are required'}, 400

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            return user.to_dict(), 200
        else:
            return {'error': 'Invalid username or password'}, 401


class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id', None)
            return {'message': 'Logged out successfully'}, 200
        return {'error': 'No user logged in'}, 401


class CheckSession(Resource):
    def get(self):
        user = get_current_user()
        if user:
            return user.to_dict(), 200
        return {'error': 'Unauthorized'}, 401


# --- Note (Resource) Endpoints ---

class NotesResource(Resource):
    def get(self):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        # Pagination params from query string (e.g. /notes?page=1&per_page=5)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        # Enforce reasonable pagination limits
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 50:
            per_page = 5

        # Query only notes owned by the logged in user
        pagination = Note.query.filter_by(user_id=user.id).order_by(Note.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'notes': [note.to_dict() for note in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages
        }, 200

    def post(self):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        data = request.get_json() or {}
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category = data.get('category', 'General').strip() or 'General'

        if not title:
            return {'error': 'Title is required'}, 400
        if not content:
            return {'error': 'Content is required'}, 400

        try:
            new_note = Note(
                title=title,
                content=content,
                category=category,
                user_id=user.id
            )
            db.session.add(new_note)
            db.session.commit()
            return new_note.to_dict(), 201
        except ValueError as ve:
            return {'error': str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': 'Failed to create note'}, 500


class NoteById(Resource):
    def get(self, id):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        # User can only view their own note
        note = Note.query.filter_by(id=id, user_id=user.id).first()
        if not note:
            return {'error': 'Note not found'}, 404

        return note.to_dict(), 200

    def patch(self, id):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        note = Note.query.filter_by(id=id, user_id=user.id).first()
        if not note:
            return {'error': 'Note not found'}, 404

        data = request.get_json() or {}

        if 'title' in data:
            title = data.get('title', '').strip()
            if not title:
                return {'error': 'Title cannot be empty'}, 400
            note.title = title

        if 'content' in data:
            content = data.get('content', '').strip()
            if not content:
                return {'error': 'Content cannot be empty'}, 400
            note.content = content

        if 'category' in data:
            note.category = data.get('category', 'General').strip() or 'General'

        try:
            db.session.commit()
            return note.to_dict(), 200
        except ValueError as ve:
            db.session.rollback()
            return {'error': str(ve)}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': 'Failed to update note'}, 500

    def delete(self, id):
        user = get_current_user()
        if not user:
            return {'error': 'Unauthorized'}, 401

        note = Note.query.filter_by(id=id, user_id=user.id).first()
        if not note:
            return {'error': 'Note not found'}, 404

        try:
            db.session.delete(note)
            db.session.commit()
            return {'message': 'Note deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            return {'error': 'Failed to delete note'}, 500


# Register API routes
api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session', '/me')

api.add_resource(NotesResource, '/notes')
api.add_resource(NoteById, '/notes/<int:id>')


@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to the Productivity Tool API',
        'status': 'healthy',
        'endpoints': {
            'auth': ['POST /signup', 'POST /login', 'DELETE /logout', 'GET /check_session'],
            'notes': ['GET /notes (paginated)', 'POST /notes', 'GET /notes/<id>', 'PATCH /notes/<id>', 'DELETE /notes/<id>']
        }
    }), 200


if __name__ == '__main__':
    app.run(port=5555, debug=True)
