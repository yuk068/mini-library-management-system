from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from db.database import engine, Base, SessionLocal
from app.models import User, Book, Borrowing

def init_db(db: Session):
    """Initializes the database, creates tables, and seeds initial data."""
    
    # 1. Create all tables defined in Base (models)
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # 2. Check if the database has seed users
    if db.query(User).count() == 0:
        print("Seeding initial data...")

        # Create Admin User
        admin_user = User(
            username="admin",
            email="admin@library.com",
            hashed_password=generate_password_hash("adminpass"),
            role="admin"
        )
        db.add(admin_user)

        # Create Regular User
        regular_user = User(
            username="user",
            email="user@library.com",
            hashed_password=generate_password_hash("userpass"),
            role="user"
        )
        db.add(regular_user)
        
        # Create Initial Books
        books = [
            Book(title="Introduction to Machine Learning with Python", author="Andreas C. Müller & Sarah Guido", genre="Computer Science", total_copies=10, available_copies=10),
            Book(title="Superintelligence: Paths, Dangers, Strategies", author="Nick Bostrom", genre="AI Ethics", total_copies=3, available_copies=3),
            Book(title="AI Engineering", author="Chip Huyen", genre="Computer Science", total_copies=8, available_copies=8),
            Book(title="—All You Zombies—", author="Robert A. Heinlein", genre="Science Fiction", total_copies=6, available_copies=6),
            Book(title="CHAINSAW MAN - Chapter 1", author="Tatsuki Fujimoto", genre="Dark Fantasy", total_copies=4, available_copies=4),
            Book(title="Do Androids Dream of Electric Sheep?", author="Philip K. Dick", genre="Science Fiction", total_copies=5, available_copies=5),
            Book(title="Deep Learning", author="Ian Goodfellow, Yoshua Bengio, & Aaron Courville", genre="Computer Science", total_copies=15, available_copies=15),
            Book(title="Frieren: Beyond Journey's End - Vol. 1", author="Kanehito Yamada", genre="Fantasy", total_copies=1, available_copies=1),
        ]
        db.add_all(books)

        db.commit()
        print("Database seeded with Admin, User, and 5 books.")
    else:
        print("Database already contains users. Skipping seed data.")


if __name__ == '__main__':
    # This block allows you to run this file directly to initialize the database
    db = SessionLocal()
    init_db(db)
    db.close()
    print("Database initialization complete.")
