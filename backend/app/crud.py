from sqlalchemy.orm import Session, joinedload # Added joinedload
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.models import User, Book, Borrowing
from db.database import get_db

### --- User and Authentication CRUD --- ###

def create_user(db: Session, username: str, email: str, password: str, role: str = 'user') -> User | None:
    """Creates a new user and adds them to the database."""
    if db.query(User).filter(or_(User.username == username, User.email == email)).first():
        return None # User already exists
    
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username, 
        email=email, 
        hashed_password=hashed_password, 
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Authenticates a user by username and password."""
    user = db.query(User).filter(User.username == username).first()
    if user and check_password_hash(user.hashed_password, password):
        return user
    return None

### --- Book CRUD (Admin Only) --- ###

def create_book(db: Session, title: str, author: str, genre: str, copies: int) -> Book:
    """Creates a new book entry."""
    new_book = Book(
        title=title, 
        author=author, 
        genre=genre, 
        total_copies=copies, 
        available_copies=copies
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

def update_book(db: Session, book_id: int, title: str, author: str, genre: str, total_copies: int) -> Book | None:
    """Updates an existing book's details."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return None
    
    # Calculate difference in copies to update available_copies safely
    copy_diff = total_copies - book.total_copies
    
    book.title = title
    book.author = author
    book.genre = genre
    book.total_copies = total_copies
    book.available_copies = book.available_copies + copy_diff
    
    # Ensure available copies doesn't drop below zero (if copies were removed)
    if book.available_copies < 0:
        book.available_copies = 0

    db.commit()
    db.refresh(book)
    return book

def delete_book(db: Session, book_id: int) -> bool:
    """Deletes a book from the catalog."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        # Also remove all related borrowing records for cleanup (optional, depends on policy)
        db.query(Borrowing).filter(Borrowing.book_id == book_id).delete()
        db.delete(book)
        db.commit()
        return True
    return False

### --- Book Search and Retrieval --- ###

def get_book_by_id(db: Session, book_id: int) -> Book | None:
    """Retrieves a book by its ID."""
    return db.query(Book).filter(Book.id == book_id).first()

def get_all_books(db: Session):
    """Retrieves all books in the catalog."""
    return db.query(Book).all()

def search_books(db: Session, query: str):
    """Searches books by title, author, or genre."""
    search_pattern = f"%{query}%"
    return db.query(Book).filter(
        or_(
            Book.title.ilike(search_pattern),
            Book.author.ilike(search_pattern),
            Book.genre.ilike(search_pattern)
        )
    ).all()

### --- Borrowing and Return Logic --- ###

def get_user_borrowings(db: Session, user_id: int):
    """Retrieves all current and historical borrowing records for a user."""
    return db.query(Borrowing).options(joinedload(Borrowing.book)).filter(Borrowing.user_id == user_id).order_by(Borrowing.borrow_date.desc()).all()

def get_active_borrowings_by_book_id(db: Session, book_id: int, user_id: int | None = None) -> list[Borrowing]:
    """Retrieves active (not returned) borrowing records for a specific book, optionally for a specific user."""
    query = db.query(Borrowing).filter(Borrowing.book_id == book_id, Borrowing.status == 'borrowed')
    if user_id is not None:
        query = query.filter(Borrowing.user_id == user_id)
    return query.all()

def borrow_book(db: Session, user_id: int, book_id: int) -> Borrowing | str:
    """Handles the book borrowing process."""
    book = get_book_by_id(db, book_id)
    if not book:
        return "Book not found."
    
    if book.available_copies <= 0:
        return "No copies are currently available."

    # Check if the user already has an active borrowing for this book
    active_borrowings = get_active_borrowings_by_book_id(db, book_id, user_id)
    if active_borrowings:
         return "You have already borrowed this book and have not returned it."

    # Decrement available copies
    book.available_copies -= 1
    
    # Create new borrowing record
    new_borrowing = Borrowing(
        user_id=user_id,
        book_id=book_id,
        status='borrowed'
    )
    
    db.add(new_borrowing)
    db.commit()
    db.refresh(new_borrowing)
    return new_borrowing

def return_book(db: Session, user_id: int, book_id: int) -> Borrowing | str:
    """Handles the book return process."""
    book = get_book_by_id(db, book_id)
    if not book:
        return "Book not found."

    # Find the most recent active borrowing by this user for this book
    active_borrowing = db.query(Borrowing).filter(
        Borrowing.user_id == user_id,
        Borrowing.book_id == book_id,
        Borrowing.status == 'borrowed'
    ).order_by(Borrowing.borrow_date.desc()).first()

    if not active_borrowing:
        return "No active borrowing record found for this user and book."

    # Increment available copies
    book.available_copies += 1
    
    # Update borrowing record
    active_borrowing.return_date = datetime.utcnow()
    active_borrowing.status = 'returned'
    
    db.commit()
    db.refresh(active_borrowing)
    return active_borrowing

def get_all_borrowing_history(db: Session):
    """Retrieves the complete history of all borrowings."""
    return db.query(Borrowing).all()

def get_all_users_with_borrowing_status(db: Session):
    """Retrieves all users and details about their borrowing activities."""
    # Eager load borrowings and the associated book to reduce database queries
    users = db.query(User).options(
        joinedload(User.borrowings).joinedload(Borrowing.book)
    ).all()
    
    user_data = []
    for user in users:
        active_borrowings = [b for b in user.borrowings if b.status == 'borrowed']
        
        user_data.append({
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'total_borrowed': len(user.borrowings),
            'active_borrowings_count': len(active_borrowings),
            'history': user.borrowings # Pass the full SQLAlchemy collection for easier template access
        })
    return user_data

def delete_user(db: Session, user_id: int) -> bool:
    """Deletes a user and all their borrowings."""
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        # Check for active borrowings
        active_borrowings = db.query(Borrowing).filter(Borrowing.user_id == user_id, Borrowing.status == 'borrowed').count()
        if active_borrowings > 0:
            return False  # Cannot delete if user has active borrowings
        db.query(Borrowing).filter(Borrowing.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        return True
    return False