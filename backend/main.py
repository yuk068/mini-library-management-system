import os
from flask import Flask
from app.routes import auth, main, admin
from app.api import api
from db.init_db import init_db
from db.database import SessionLocal

def create_app():
    """Application factory function."""
    app = Flask(__name__, template_folder='templates')
    
    # Configuration
    app.config['SECRET_KEY'] = 'a-super-secret-key-for-session-management'
    
    # Ensure the database is initialized
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

    # Register Blueprints
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(api)
    
    return app

if __name__ == '__main__':
    # Set the working directory to the backend folder for correct path resolution
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = create_app()
    print("Starting Flask application...")
    app.run(debug=False)
