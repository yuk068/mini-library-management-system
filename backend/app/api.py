from flask import Blueprint, request, jsonify
from backend.app.crud import (
    get_all_books, get_book_by_id, create_book, update_book, delete_book,
    get_all_users_with_borrowing_status, get_user_borrowings, borrow_book, return_book,
    delete_user
)
from backend.app.utils import login_required, role_required
from backend.db.database import get_db

api = Blueprint('api', __name__, url_prefix='/api')

# --- Book Endpoints ---
@api.route('/books', methods=['GET'])
@login_required
@role_required('admin')
def api_get_books():
    db = next(get_db())
    books = get_all_books(db)
    return jsonify([{
        'id': b.id, 'title': b.title, 'author': b.author, 'genre': b.genre,
        'total_copies': b.total_copies, 'available_copies': b.available_copies
    } for b in books])

@api.route('/books/<int:book_id>', methods=['GET'])
@login_required
@role_required('admin')
def api_get_book(book_id):
    db = next(get_db())
    book = get_book_by_id(db, book_id)
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify({
        'id': book.id, 'title': book.title, 'author': book.author, 'genre': book.genre,
        'total_copies': book.total_copies, 'available_copies': book.available_copies
    })

@api.route('/books', methods=['POST'])
@login_required
@role_required('admin')
def api_create_book():
    db = next(get_db())
    data = request.get_json()
    book = create_book(db, data['title'], data['author'], data['genre'], data['copies'])
    return jsonify({'id': book.id}), 201

@api.route('/books/<int:book_id>', methods=['PUT'])
@login_required
@role_required('admin')
def api_update_book(book_id):
    db = next(get_db())
    data = request.get_json()
    book = update_book(db, book_id, data['title'], data['author'], data['genre'], data['copies'])
    if not book:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify({'id': book.id})

@api.route('/books/<int:book_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def api_delete_book(book_id):
    db = next(get_db())
    if delete_book(db, book_id):
        return jsonify({'result': 'success'})
    return jsonify({'error': 'Book not found'}), 404

# --- User Endpoints ---
@api.route('/users', methods=['GET'])
@login_required
@role_required('admin')
def api_get_users():
    db = next(get_db())
    users = get_all_users_with_borrowing_status(db)
    return jsonify(users)

@api.route('/users/<int:user_id>/borrowings', methods=['GET'])
@login_required
@role_required('admin')
def api_get_user_borrowings(user_id):
    db = next(get_db())
    borrowings = get_user_borrowings(db, user_id)
    return jsonify([
        {'id': b.id, 'book_id': b.book_id, 'borrow_date': b.borrow_date.isoformat(),
         'return_date': b.return_date.isoformat() if b.return_date else None, 'status': b.status}
        for b in borrowings
    ])

# --- Borrowing Endpoints (for users) ---
@api.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def api_borrow_book(book_id):
    db = next(get_db())
    user_id = request.json.get('user_id')
    result = borrow_book(db, user_id, book_id)
    if isinstance(result, str):
        return jsonify({'error': result}), 400
    return jsonify({'id': result.id})

@api.route('/return/<int:book_id>', methods=['POST'])
@login_required
def api_return_book(book_id):
    db = next(get_db())
    user_id = request.json.get('user_id')
    result = return_book(db, user_id, book_id)
    if isinstance(result, str):
        return jsonify({'error': result}), 400
    return jsonify({'id': result.id})

@api.route('/users/me', methods=['DELETE'])
@login_required
def api_delete_own_account():
    db = next(get_db())
    user_id = getattr(request, 'user_id', None) or (getattr(request, 'user', None) and request.user.id) or None
    # Fallback: try session if using Flask-Login or session
    from flask import session
    if not user_id:
        user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    result = delete_user(db, user_id)
    if result:
        session.clear()
        return jsonify({'result': 'Account deleted'})
    # Check if user exists and has active borrowings
    from backend.app.models import Borrowing
    active_borrowings = db.query(Borrowing).filter(Borrowing.user_id == user_id, Borrowing.status == 'borrowed').count()
    if active_borrowings > 0:
        return jsonify({'error': 'You cannot delete your account while you have borrowed books. Please return all books first.'}), 400
    return jsonify({'error': 'User not found'}), 404
