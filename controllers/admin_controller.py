from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.product_service import ProductService
from services.auth_service import AuthService
from services.order_service import OrderService
from models.database import Order
from functools import wraps
from werkzeug.utils import secure_filename
import os

admin_bp = Blueprint('admin', __name__)

UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('username') == 'admin' or session.get('user_type') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    if request.method == 'POST':
        # Update stock for products
        for key, value in request.form.items():
            if key.startswith('stock_'):
                product_id = int(key.split('_')[1])
                try:
                    new_stock = int(value)
                    ProductService.update_stock(product_id, new_stock - ProductService.get_product_by_id(product_id).stock)
                except Exception:
                    flash(f'Invalid stock value for product {product_id}', 'error')
        flash('Stock values updated successfully!', 'success')
        return redirect(url_for('admin.admin_panel'))
    products = ProductService.get_all_products()
    low_stock_products = ProductService.get_low_stock_products()
    return render_template('admin_panel.html', products=products, low_stock_products=low_stock_products)

@admin_bp.route('/update_stock/<int:product_id>', methods=['POST'])
@admin_required
def update_stock(product_id):
    try:
        new_stock = int(request.form.get('quantity', 0))
        ProductService.update_stock(product_id, new_stock - ProductService.get_product_by_id(product_id).stock)
        flash('Stock updated successfully.', 'success')
    except Exception:
        flash('Failed to update stock.', 'error')
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/admin/products')
@admin_required
def admin_products():
    products = ProductService.get_all_products()
    return render_template('admin_products.html', products=products)

@admin_bp.route('/admin/products/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price', type=float)
        description = request.form.get('description')
        stock = request.form.get('stock', type=int)
        category = request.form.get('category')
        image_file = request.files.get('image')
        image_filename = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(image_path)
            image_filename = filename
        success, message = ProductService.create_product(
            name=name,
            price=price,
            description=description,
            image=image_filename or '',
            stock=stock,
            category=category
        )
        if success:
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.admin_products'))
        else:
            flash(message, 'error')
    return render_template('admin_product_form.html', action='Add')

@admin_bp.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('admin.admin_products'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price', type=float)
        description = request.form.get('description')
        stock = request.form.get('stock', type=int)
        category = request.form.get('category')
        image_file = request.files.get('image')
        
        image_filename = product.image
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image_file.save(image_path)
            image_filename = filename

        success, message = ProductService.update_product(
            product_id,
            name=name,
            price=price,
            description=description,
            image=image_filename,
            stock=stock,
            category=category
        )
        if success:
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin.admin_products'))
        else:
            flash(message, 'error')
    
    return render_template('admin_product_form.html', action='Edit', product=product)

@admin_bp.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    success, message = ProductService.delete_product(product_id)
    if success:
        flash('Product deleted successfully!', 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin.admin_products'))

# Order Management Routes
@admin_bp.route('/admin/orders')
@admin_required
def admin_orders():
    """Display all orders for the admin."""
    orders = OrderService.get_all_orders()
    return render_template('admin_orders.html', orders=orders)

@admin_bp.route('/admin/order/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """Display details of a single order for the admin."""
    order = Order.query.get_or_404(order_id)
    return render_template('admin_order_detail.html', order=order)

@admin_bp.route('/admin/order/approve/<int:order_id>', methods=['POST'])
@admin_required
def approve_order(order_id):
    """Approve an order."""
    success, message = OrderService.update_order_status(order_id, 'Approved')
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin.admin_order_detail', order_id=order_id))

@admin_bp.route('/admin/order/reject/<int:order_id>', methods=['POST'])
@admin_required
def reject_order(order_id):
    """Reject an order."""
    success, message = OrderService.update_order_status(order_id, 'Rejected')
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('admin.admin_order_detail', order_id=order_id)) 