from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import AuthService
from services.cart_service import CartService
from functools import wraps
from models.database import User

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        # Unified user login
        success, message = AuthService.login_user(username, password)
        
        if success:
            # Merge session cart to DB cart after successful login
            user_id = session.get('user_id')
            if user_id:
                CartService.merge_session_cart_to_db(user_id)

            flash(f"Welcome, {session.get('first_name', username)}!", 'success')
            if session.get('user_type') == 'admin':
                return redirect(url_for('admin.admin_panel'))
            else:
                return redirect(url_for('product.index'))
        else:
            flash(message, 'error')
    
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle user registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('Please fill in all required fields.', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')
        
        success, message = AuthService.register_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address
        )
        
        if success:
            flash(message, 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'error')
    
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('product.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('profile.html', user=user)

@auth_bp.route('/edit-profile', methods=['POST'])
@login_required
def edit_profile():
    """Update user profile"""
    user_id = session.get('user_id')
    
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    
    success, message = AuthService.update_user_profile(
        user_id, first_name, last_name, phone, address
    )
    
    if success:
        # Update session with new user info
        user = User.query.get(user_id)
        session['first_name'] = user.first_name
        session['last_name'] = user.last_name
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('auth.profile'))

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    user_id = session.get('user_id')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate form data
    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required!', 'error')
        return redirect(url_for('auth.profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match!', 'error')
        return redirect(url_for('auth.profile'))
    
    success, message = AuthService.change_password(user_id, current_password, new_password)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('auth.profile')) 