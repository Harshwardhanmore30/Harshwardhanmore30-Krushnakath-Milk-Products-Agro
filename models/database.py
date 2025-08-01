from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and user management"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    user_type = db.Column(db.String(20), nullable=False, default='user')  # 'user' or 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Product(db.Model):
    """Product model for dairy products"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(200), nullable=False)
    stock = db.Column(db.Integer, default=100)
    category = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with product specifications
    specifications = db.relationship('ProductSpecification', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductSpecification(db.Model):
    """Product specification model for nutritional information"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    feature = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<ProductSpecification {self.feature}: {self.value}>'

class MLProduct(db.Model):
    """ML Product model for recommendation system"""
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    combined_features = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<MLProduct {self.product_name}>'

class Feedback(db.Model):
    """Feedback model for customer feedback"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.name}>'

class Cart(db.Model):
    """Cart model, each user has one cart"""
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('cart', uselist=False))
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Cart for User {self.user_id}>'

class CartItem(db.Model):
    """Individual items within a cart"""
    __tablename__ = 'cart_item'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Prevent duplicate products in the same cart
    __table_args__ = (db.UniqueConstraint('cart_id', 'product_id', name='_cart_product_uc'),)

    product = db.relationship('Product')

    def __repr__(self):
        return f'<CartItem Product {self.product_id} (Qty: {self.quantity})>'

class Order(db.Model):
    """Order model"""
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending Verification')
    shipping_address = db.Column(db.Text, nullable=False)
    transaction_id = db.Column(db.String(255), nullable=True)
    payment_screenshot = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.id}>'

class OrderItem(db.Model):
    """Individual items within an order"""
    __tablename__ = 'order_item'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False) # Price at the time of purchase

    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product')

    def __repr__(self):
        return f'<OrderItem {self.id} for Order {self.order_id}>' 