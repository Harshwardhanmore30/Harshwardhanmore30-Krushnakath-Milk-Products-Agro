from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from services.product_service import ProductService
from services.auth_service import AuthService
from services.cart_service import CartService
from functools import wraps

product_bp = Blueprint('product', __name__)

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_cart_count():
    """Helper to get cart count for logged-in users or guests."""
    user_id = session.get('user_id')
    if user_id:
        return CartService.get_cart_count(user_id)
    else:
        return CartService.get_session_cart_count()

@product_bp.route('/')
def index():
    """Home page with featured products"""
    products = ProductService.get_all_products()
    return render_template('index.html', products=products, cart_count=get_cart_count())

@product_bp.route('/products')
def products():
    """Display all products"""
    products = ProductService.get_all_products()
    return render_template('dairy.html', products=products, cart_count=get_cart_count())

@product_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    """Display product details"""
    product = ProductService.get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('product.products'))
    
    # Get ML recommendations and fetch full product details by name
    ml_recs = ProductService.get_ml_recommendations(product.name)
    recommendation_names = [rec['product_name'] for rec in ml_recs]
    
    # Fetch fresh product data for recommendations, excluding the current product
    recommendations = ProductService.get_products_by_names(recommendation_names)
    recommendations = [rec for rec in recommendations if rec.id != product_id]
    
    return render_template('product.html', 
                         product=product, 
                         recommendations=recommendations,
                         cart_count=get_cart_count())

@product_bp.route('/search')
def search():
    """Search products"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('product.products'))
    
    products = ProductService.search_products(query)
    
    return render_template('dairy.html', 
                         products=products, 
                         search_query=query,
                         cart_count=get_cart_count())

@product_bp.route('/category/<category>')
def category(category):
    """Display products by category"""
    products = ProductService.get_products_by_category(category)
    
    return render_template('dairy.html', 
                         products=products, 
                         category=category,
                         cart_count=get_cart_count())

@product_bp.route('/api/products')
def api_products():
    """API endpoint to get products"""
    products = ProductService.get_all_products()
    product_list = []
    
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'description': product.description,
            'image': product.image,
            'stock': product.stock,
            'category': product.category
        })
    
    return jsonify(product_list)

@product_bp.route('/api/product/<int:product_id>')
def api_product_detail(product_id):
    """API endpoint to get product details"""
    product = ProductService.get_product_by_id(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    product_data = {
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'description': product.description,
        'image': product.image,
        'stock': product.stock,
        'category': product.category,
        'specifications': [
            {
                'feature': spec.feature,
                'value': spec.value
            } for spec in product.specifications
        ]
    }
    
    return jsonify(product_data) 