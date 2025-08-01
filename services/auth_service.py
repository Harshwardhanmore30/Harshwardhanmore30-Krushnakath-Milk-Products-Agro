from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db, User
from flask import session
import re

class AuthService:
    """Service class for authentication operations"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        return True, "Password is valid"
    
    @staticmethod
    def register_user(username, email, password, first_name=None, last_name=None, phone=None, address=None):
        """Register a new user"""
        try:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return False, "Username already exists"
            
            if User.query.filter_by(email=email).first():
                return False, "Email already registered"
            
            # Validate email
            if not AuthService.validate_email(email):
                return False, "Invalid email format"
            
            # Validate password
            is_valid, message = AuthService.validate_password(password)
            if not is_valid:
                return False, message
            
            # Create new user
            password_hash = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                address=address
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            return True, "Registration successful"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Registration failed: {str(e)}"
    
    @staticmethod
    def login_user(username, password):
        """Authenticate user login"""
        try:
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                if not user.is_active:
                    return False, "Account is deactivated"
                
                # Store user info in session
                session['user_id'] = user.id
                session['username'] = user.username
                session['email'] = user.email
                session['first_name'] = user.first_name
                session['last_name'] = user.last_name
                session['user_type'] = user.user_type
                
                return True, "Login successful"
            else:
                return False, "Invalid username or password"
                
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    @staticmethod
    def logout_user():
        """Logout user and clear session"""
        try:
            session.clear()
            return True, "Logout successful"
        except Exception as e:
            return False, f"Logout failed: {str(e)}"
    
    @staticmethod
    def is_authenticated():
        """Check if user is authenticated"""
        return 'user_id' in session
    
    @staticmethod
    def get_current_user():
        """Get current user from session"""
        if AuthService.is_authenticated():
            return User.query.get(session['user_id'])
        return None
    
    @staticmethod
    def update_user_profile(user_id, first_name=None, last_name=None, phone=None, address=None):
        """Update user profile information"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if phone is not None:
                user.phone = phone
            if address is not None:
                user.address = address
            
            db.session.commit()
            return True, "Profile updated successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Profile update failed: {str(e)}"
    
    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                return False, "User not found"
            
            # Verify current password
            if not check_password_hash(user.password_hash, current_password):
                return False, "Current password is incorrect"
            
            # Validate new password
            is_valid, message = AuthService.validate_password(new_password)
            if not is_valid:
                return False, message
            
            # Hash and update new password
            new_password_hash = generate_password_hash(new_password)
            user.password_hash = new_password_hash
            
            db.session.commit()
            return True, "Password changed successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Password change failed: {str(e)}" 