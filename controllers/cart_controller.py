from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services.cart_service import CartService
from services.auth_service import AuthService
from services.order_service import OrderService
from models.database import User  # Import the User model
from functools import wraps
import os
from werkzeug.utils import secure_filename
from config import Config

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/cart')
def view_cart():
    """Display shopping cart for logged-in users only."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your cart.', 'error')
        return redirect(url_for('auth.login'))

    cart_items, total = CartService.get_cart_items(user_id)
    cart_count = CartService.get_cart_count(user_id)

    return render_template('cart.html',
                         cart_items=cart_items,
                         total=total,
                         cart_count=cart_count)

@cart_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add an item to the cart - requires login."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to add items to your cart.', 'error')
        return redirect(url_for('auth.login'))

    quantity = request.form.get('quantity', 1, type=int)
    success, message = CartService.add_to_cart(user_id, product_id, quantity)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(request.referrer or url_for('product.index'))

@cart_bp.route('/cart/clear', methods=['POST'])
def clear_cart():
    """Clear entire cart - requires login."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access your cart.', 'error')
        return redirect(url_for('auth.login'))

    success, message = CartService.clear_cart(user_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update item quantity in cart - requires login."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access your cart.', 'error')
        return redirect(url_for('auth.login'))

    quantity = request.form.get('quantity', type=int)
    if quantity is None or quantity < 0:
        flash('Invalid quantity.', 'error')
        return redirect(url_for('cart.view_cart'))

    success, message = CartService.update_item_quantity(user_id, product_id, quantity)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove item from cart - requires login."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access your cart.', 'error')
        return redirect(url_for('auth.login'))

    success, message = CartService.remove_item_from_cart(user_id, product_id)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Handle checkout process"""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to proceed with checkout.', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'GET':
        cart_items, total = CartService.get_cart_items(user_id)
        
        if not cart_items:
            flash('Your cart is empty.', 'error')
            return redirect(url_for('cart.view_cart'))
        
        # Fetch the user object to pre-fill form
        user = User.query.get(user_id)
        
        cart_count = CartService.get_cart_count(user_id)
        return render_template('checkout.html',
                             user=user,  # Pass user to template
                             cart_items=cart_items,
                             total=total,
                             cart_count=cart_count)
    
    elif request.method == 'POST':
        # This is now the order creation step
        form = request.form
        screenshot = request.files.get('payment_screenshot')

        # Basic validation
        if not form.get('transaction_id') or not screenshot:
            flash('Transaction ID and payment screenshot are required.', 'error')
            return redirect(url_for('cart.checkout'))
        
        # --- Handle File Upload ---
        if screenshot.filename == '':
            flash('No screenshot selected.', 'error')
            return redirect(url_for('cart.checkout'))

        # Secure the filename and save the file
        filename = secure_filename(screenshot.filename)
        # Ensure the upload folder exists
        upload_folder = Config.UPLOADS_FOLDER
        os.makedirs(upload_folder, exist_ok=True)
        # Save the file
        screenshot_path = os.path.join(upload_folder, filename)
        screenshot.save(screenshot_path)
        
        # --- Create Full Shipping Address ---
        shipping_address = f"Name: {form.get('name')}\n" \
                           f"Email: {form.get('email')}\n" \
                           f"Contact: {form.get('contact')}\n" \
                           f"Address: {form.get('address')}"

        # --- Call Order Service to Create Order ---
        success, message = OrderService.create_order(
            user_id=user_id,
            shipping_address=shipping_address,
            transaction_id=form.get('transaction_id'),
            payment_screenshot_filename=filename # Just save the filename
        )
        
        if success:
            flash("Your order has been placed successfully and is pending verification!", 'success')
            # Redirect to a new "my_orders" page, which we will create next
            return redirect(url_for('order.my_orders'))
        else:
            flash(f"Error placing order: {message}", 'error')
            return redirect(url_for('cart.checkout'))

@cart_bp.route('/cart/validate')
def validate_cart():
    """Validate cart items"""
    is_valid, errors = CartService.validate_cart()

    if not is_valid:
        for error in errors:
            flash(error, 'error')
    else:
        flash('Cart is valid.', 'success')

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/api/cart/count')
def api_cart_count():
    """API endpoint to get cart count"""
    user_id = session.get('user_id')
    if user_id:
        count = CartService.get_cart_count(user_id)
    else:
        count = CartService.get_session_cart_count()

    return jsonify({'count': count})