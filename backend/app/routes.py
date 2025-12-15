from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.crud import (
    authenticate_user, create_user, search_books, get_all_books, 
    borrow_book, return_book, get_user_borrowings, 
    create_book, update_book, delete_book, get_book_by_id,
    get_all_users_with_borrowing_status # <-- Added new function
)
from app.utils import login_required, role_required
from db.database import get_db

# Create blueprints for modular routing
auth = Blueprint('auth', __name__, url_prefix='/')
main = Blueprint('main', __name__, url_prefix='/')
admin = Blueprint('admin', __name__, url_prefix='/admin')

### --- AUTH ROUTES --- ###

@auth.route('/', methods=['GET', 'POST'])
def index():
    """Login and Registration page."""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')
        db_generator = get_db()
        db = next(db_generator)

        try:
            if action == 'login':
                username = request.form.get('username')
                password = request.form.get('password')
                user = authenticate_user(db, username, password)
                
                if user:
                    session.clear()
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['user_role'] = user.role
                    flash(f"Welcome, {user.username}!", "success")
                    return redirect(url_for('main.dashboard'))
                else:
                    flash("Invalid username or password.", "error")
            
            elif action == 'register':
                username = request.form.get('reg_username')
                email = request.form.get('reg_email')
                password = request.form.get('reg_password')
                
                if not (username and email and password):
                    flash("Please fill in all registration fields.", "error")
                    return render_template('index.html')

                user = create_user(db, username, email, password)
                
                if user:
                    flash("Registration successful. Please log in.", "success")
                else:
                    flash("Username or email already in use.", "error")
        finally:
            next(db_generator, None)
            
    return render_template('index.html')

@auth.route('/logout')
@login_required
def logout():
    """Logs out the user."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('auth.index'))

### --- MAIN LIBRARY ROUTES (User/Admin) --- ###

@main.route('/dashboard')
@login_required
def dashboard():
    """Main library dashboard: search, browse, view borrowings."""
    db_generator = get_db()
    db = next(db_generator)
    
    try:
        query = request.args.get('query')
        if query:
            books = search_books(db, query)
        else:
            books = get_all_books(db)
        
        user_borrowings = get_user_borrowings(db, session['user_id'])
        
    finally:
        next(db_generator, None)

    return render_template(
        'dashboard.html', 
        books=books, 
        borrowings=user_borrowings, 
        role=session.get('user_role')
    )

@main.route('/borrow/<int:book_id>')
@login_required
def borrow(book_id):
    """Handles book borrowing request."""
    db_generator = get_db()
    db = next(db_generator)
    
    try:
        result = borrow_book(db, session['user_id'], book_id)
        if isinstance(result, str):
            flash(f"Borrow failed: {result}", "error")
        else:
            flash(f"Successfully borrowed '{result.book.title}'.", "success")
    finally:
        next(db_generator, None)
        
    return redirect(url_for('main.dashboard'))

@main.route('/return/<int:book_id>')
@login_required
def return_book_route(book_id):
    """Handles book return request."""
    db_generator = get_db()
    db = next(db_generator)
    
    try:
        result = return_book(db, session['user_id'], book_id)
        if isinstance(result, str):
            flash(f"Return failed: {result}", "error")
        else:
            flash(f"Successfully returned '{result.book.title}'.", "success")
    finally:
        next(db_generator, None)
        
    return redirect(url_for('main.dashboard'))

### --- ADMIN ROUTES --- ###

@admin.route('/panel', methods=['GET'])
@role_required('admin')
def admin_panel():
    """Admin panel for managing books."""
    db_generator = get_db()
    db = next(db_generator)
    
    try:
        books = get_all_books(db)
        user_logs = get_all_users_with_borrowing_status(db)
    finally:
        next(db_generator, None)
    return render_template('admin_panel.html', books=books, user_logs=user_logs)

@admin.route('/logs', methods=['GET']) # <-- NEW ROUTE
@role_required('admin')
def admin_logs():
    """Admin view for user borrowing logs and user management info."""
    db_generator = get_db()
    db = next(db_generator)

    try:
        # Fetch detailed user and borrowing data
        user_logs = get_all_users_with_borrowing_status(db)
    finally:
        next(db_generator, None)
    
    return render_template('admin_logs.html', user_logs=user_logs)


@admin.route('/book/add', methods=['POST'])
@role_required('admin')
def add_book():
    """Handles adding a new book."""
    db_generator = get_db()
    db = next(db_generator)

    try:
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        copies = int(request.form.get('copies'))
        
        create_book(db, title, author, genre, copies)
        flash(f"Book '{title}' added successfully.", "success")
    
    except Exception as e:
        flash(f"Error adding book: {e}", "error")
    finally:
        next(db_generator, None)

    return redirect(url_for('admin.admin_panel'))

@admin.route('/book/edit/<int:book_id>', methods=['POST'])
@role_required('admin')
def edit_book(book_id):
    """Handles editing an existing book."""
    db_generator = get_db()
    db = next(db_generator)
    
    try:
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        copies = int(request.form.get('copies'))

        book = update_book(db, book_id, title, author, genre, copies)
        if book:
            flash(f"Book '{book.title}' updated successfully.", "success")
        else:
            flash("Book not found for update.", "error")
            
    except Exception as e:
        flash(f"Error editing book: {e}", "error")
    finally:
        next(db_generator, None)

    return redirect(url_for('admin.admin_panel'))

@admin.route('/book/delete/<int:book_id>', methods=['POST'])
@role_required('admin')
def delete_book_route(book_id):
    """Handles deleting a book."""
    db_generator = get_db()
    db = next(db_generator)
    
    try:
        if delete_book(db, book_id):
            flash("Book deleted successfully.", "success")
        else:
            flash("Book not found for deletion.", "error")
            
    except Exception as e:
        flash(f"Error deleting book: {e}", "error")
    finally:
        next(db_generator, None)

    return redirect(url_for('admin.admin_panel'))
