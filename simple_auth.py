from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User, db
import logging

auth_simple = Blueprint('auth_simple', __name__)

@auth_simple.route('/simple-login', methods=['GET', 'POST'])
def login():
    """Handle user login with static credentials"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # Default credentials check
        if username == 'budd' and password == 'dwyer':
            # Check if user exists in DB
            user = User.query.filter_by(username='budd').first()
            
            # Create user if it doesn't exist
            if not user:
                try:
                    user = User(username='budd', email='budd@example.com')
                    user.password_hash = generate_password_hash('dwyer')
                    db.session.add(user)
                    db.session.commit()
                    logging.info("Default user created during login")
                except Exception as e:
                    logging.error(f"Error creating default user: {str(e)}")
                    flash('Error setting up user account. Please try again.', 'danger')
                    return render_template('login_simple.html')
            
            # Log in the user
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template('login_simple.html')

@auth_simple.route('/simple-logout')
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth_simple.login'))