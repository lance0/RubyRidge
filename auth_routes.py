from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from models import User, db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login requests"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        # Check if the user exists and password is correct
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return render_template('login.html')

        # If validation passes, log in the user
        login_user(user, remember=remember)
        
        # Update last login time
        user.last_login = db.func.now()
        db.session.commit()
        
        # Redirect to the page the user was trying to access or home
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('home'))
    
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration requests"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not username or not email or not password:
            flash('All fields are required', 'danger')
            return render_template('register.html')
            
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | 
                                         (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=password
        )
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@auth.route('/profile')
@login_required
def profile():
    """Display user profile information"""
    user_ammo = current_user.ammo_boxes.all()
    user_firearms = current_user.firearms.all()
    user_range_trips = current_user.range_trips.all()
    
    # Calculate total rounds and inventory value
    total_rounds = sum(box.total_rounds for box in user_ammo)
    total_value = sum(box.purchase_price * box.quantity for box in user_ammo if box.purchase_price)
    
    return render_template('profile.html', 
                         user=current_user,
                         ammo_boxes=user_ammo,
                         firearms=user_firearms,
                         range_trips=user_range_trips,
                         total_rounds=total_rounds,
                         total_value=total_value)