from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, current_user, login_required
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
    
@quick_auth.route('/account-settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    """Display and process account settings page"""
    if request.method == 'POST':
        # Update user information
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.first_name = request.form.get('first_name') or None
        current_user.last_name = request.form.get('last_name') or None
        
        # Check if user wants to change password
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password and confirm_password:
            # Check if current password is correct
            if current_user.check_password(current_password):
                # Check if new passwords match
                if new_password == confirm_password:
                    # Update password
                    current_user.password_hash = generate_password_hash(new_password)
                    flash('Password updated successfully.', 'success')
                else:
                    flash('New passwords do not match.', 'danger')
                    return render_template('account_settings.html')
            else:
                flash('Current password is incorrect.', 'danger')
                return render_template('account_settings.html')
        
        # Save changes
        try:
            db.session.commit()
            flash('Account settings updated successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating account settings: {str(e)}', 'danger')
            
    return render_template('account_settings.html')
    
@quick_auth.route('/update-account', methods=['POST'])
@login_required
def update_account():
    """Process account settings form submission"""
    # Update user information
    current_user.username = request.form.get('username')
    current_user.email = request.form.get('email')
    current_user.first_name = request.form.get('first_name') or None
    current_user.last_name = request.form.get('last_name') or None
    
    # Check if user wants to change password
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if current_password and new_password and confirm_password:
        # For now, allow changing password without verifying old one (since it's a demo account)
        if new_password == confirm_password:
            # Update password
            current_user.password_hash = generate_password_hash(new_password)
            flash('Password updated successfully.', 'success')
        else:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('quick_auth.account_settings'))
    
    # Save changes
    try:
        db.session.commit()
        flash('Account settings updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating account settings: {str(e)}', 'danger')
        
    return redirect(url_for('quick_auth.account_settings'))