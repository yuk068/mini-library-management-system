from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """Decorator to check if a user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You must be logged in to access this page.", "error")
            return redirect(url_for('auth.index'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorator to check if the logged-in user has the required role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] != required_role:
                flash("Access denied. You do not have the required permissions.", "error")
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
