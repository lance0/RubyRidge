from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash
from models import db, User

quick_auth = Blueprint('quick_auth', __name__)

@quick_auth.route('/quick-login', methods=['GET', 'POST'])
def quick_login():
    """Super simple login that creates and logs in as budd/dwyer"""
    
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # Try to get the user first
        user = User.query.filter_by(username='budd').first()
        
        # If no user exists, create one
        if not user:
            try:
                user = User(username='budd', email='budd@example.com')
                user.password_hash = generate_password_hash('dwyer')
                db.session.add(user)
                db.session.commit()
                flash('Default user created successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error creating user: {str(e)}', 'danger')
                return render_template('quick_login.html')
        
        # Log in the user
        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('home'))
        
    return render_template('quick_login.html')

@quick_auth.route('/quick-logout')
def quick_logout():
    """Simple logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('quick_auth.quick_login'))