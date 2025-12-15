from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class User(Base):
    """Represents a user in the library system (member or admin)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user") # 'user' or 'admin'
    
    borrowings = relationship("Borrowing", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

class Book(Base):
    """Represents a book in the library catalog."""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    genre = Column(String, index=True)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    
    borrowings = relationship("Borrowing", back_populates="book")

    def __repr__(self):
        return f"<Book(title='{self.title}', author='{self.author}')>"

class Borrowing(Base):
    """Represents a borrowing record (activity log)."""
    __tablename__ = "borrowings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    borrow_date = Column(DateTime, default=datetime.utcnow)
    return_date = Column(DateTime, nullable=True)
    
    # Status: 'borrowed' or 'returned' (if return_date is set)
    # We use a separate column for clarity in simple applications
    status = Column(String, default='borrowed') # 'borrowed', 'returned'

    user = relationship("User", back_populates="borrowings")
    book = relationship("Book", back_populates="borrowings")

    def __repr__(self):
        return f"<Borrowing(id={self.id}, user_id={self.user_id}, book_id={self.book_id}, status='{self.status}')>"
