from flask import session
from models.database import db, Product, User, Cart, CartItem
from services.auth_service import AuthService

class CartService:
    """Service class for database-driven shopping cart operations"""

    @staticmethod
    def get_or_create_cart(user_id):
        """Get the user's cart, or create one if it doesn't exist."""
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()
        return cart

    @staticmethod
    def add_to_cart(user_id, product_id, quantity=1):
        """Add a product to the user's database cart."""
        try:
            cart = CartService.get_or_create_cart(user_id)
            product = Product.query.get(product_id)

            if not product:
                return False, "Product not found."
            if product.stock < quantity:
                return False, f"Insufficient stock for {product.name}. Only {product.stock} available."

            cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

            if cart_item:
                # Item exists, update quantity
                new_quantity = cart_item.quantity + quantity
                if product.stock < new_quantity:
                    return False, f"Cannot add {quantity} more. Only {product.stock - cart_item.quantity} additional units available."
                cart_item.quantity = new_quantity
            else:
                # Item does not exist, create new
                cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
                db.session.add(cart_item)
            
            db.session.commit()
            return True, f"Added {quantity} x {product.name} to your cart."

        except Exception as e:
            db.session.rollback()
            return False, f"Error adding to cart: {str(e)}"

    @staticmethod
    def remove_item_from_cart(user_id, product_id):
        """Remove a product from the user's cart."""
        try:
            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart:
                return False, "Cart not found."

            cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
                return True, "Product removed from cart."
            else:
                return False, "Product not in cart."
        except Exception as e:
            db.session.rollback()
            return False, f"Error removing item: {str(e)}"

    @staticmethod
    def update_item_quantity(user_id, product_id, quantity):
        """Update a product's quantity in the user's cart."""
        try:
            if quantity <= 0:
                return CartService.remove_item_from_cart(user_id, product_id)

            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart:
                return False, "Cart not found."

            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found."
            if product.stock < quantity:
                return False, f"Insufficient stock. Only {product.stock} available."

            cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if cart_item:
                cart_item.quantity = quantity
                db.session.commit()
                return True, "Cart quantity updated."
            else:
                return False, "Product not in cart."
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating quantity: {str(e)}"

    @staticmethod
    def clear_cart(user_id):
        """Clear all items from a user's cart."""
        try:
            cart = Cart.query.filter_by(user_id=user_id).first()
            if cart:
                CartItem.query.filter_by(cart_id=cart.id).delete()
                db.session.commit()
            return True, "Cart cleared successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Error clearing cart: {str(e)}"

    @staticmethod
    def get_cart_items(user_id):
        """Get all items from a user's cart with product details."""
        try:
            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart:
                return [], 0.0

            cart_items = []
            total = 0.0
            for item in cart.items:
                product = item.product
                if product:
                    item_total = product.price * item.quantity
                    cart_items.append({
                        'product_id': product.id,
                        'name': product.name,
                        'price': product.price,
                        'quantity': item.quantity,
                        'total': item_total,
                        'image': product.image,
                        'stock': product.stock,
                        'category': product.category,
                    })
                    total += item_total
            
            return cart_items, total
        except Exception as e:
            print(f"Error getting cart items: {e}")
            return [], 0.0

    @staticmethod
    def get_cart_count(user_id):
        """Get the total number of items in a user's cart."""
        try:
            cart = Cart.query.filter_by(user_id=user_id).first()
            if not cart:
                return 0
            
            # Sum the quantity of all items in the cart
            total_items = db.session.query(db.func.sum(CartItem.quantity)).filter(CartItem.cart_id == cart.id).scalar()
            return total_items or 0
        except Exception as e:
            print(f"Error getting cart count: {e}")
            return 0
            
    @staticmethod
    def merge_session_cart_to_db(user_id):
        """Merge cart from session into the user's DB cart after login."""
        session_cart = session.pop('cart', None)
        if not session_cart:
            return

        print(f"Merging session cart for user {user_id}: {session_cart}")
        for product_id, quantity in session_cart.items():
            # Use the existing add_to_cart logic to handle merging
            # This correctly checks for stock and existing items
            CartService.add_to_cart(user_id=user_id, product_id=int(product_id), quantity=quantity)
        
        session.modified = True
        print("Session cart merged and removed.")

    # --- Session-based (Guest) Cart Methods ---

    @staticmethod
    def get_session_cart():
        """Get the guest cart from the session."""
        return session.get('cart', {})

    @staticmethod
    def add_to_session_cart(product_id, quantity=1):
        """Add a product to the guest's session cart."""
        try:
            cart = CartService.get_session_cart()
            product = Product.query.get(product_id)

            if not product:
                return False, "Product not found"
            if product.stock < quantity:
                return False, f"Insufficient stock. Only {product.stock} available."
            
            product_id_str = str(product_id)
            if product_id_str in cart:
                new_quantity = cart[product_id_str] + quantity
                if product.stock < new_quantity:
                    return False, f"Cannot add {quantity} more. Only {product.stock - cart[product_id_str]} additional units available."
                cart[product_id_str] = new_quantity
            else:
                cart[product_id_str] = quantity
            
            session['cart'] = cart
            session.modified = True
            return True, f"Added {quantity} x {product.name} to your cart."
        except Exception as e:
            return False, f"Error adding to cart: {str(e)}"

    @staticmethod
    def remove_item_from_session_cart(product_id):
        """Remove a product from the guest's session cart."""
        try:
            cart = CartService.get_session_cart()
            product_id_str = str(product_id)
            if product_id_str in cart:
                del cart[product_id_str]
                session['cart'] = cart
                session.modified = True
                return True, "Product removed from cart."
            else:
                return False, "Product not in cart."
        except Exception as e:
            return False, f"Error removing from cart: {str(e)}"

    @staticmethod
    def update_session_item_quantity(product_id, quantity):
        """Update a product's quantity in the guest's session cart."""
        try:
            if quantity <= 0:
                return CartService.remove_item_from_session_cart(product_id)
            
            cart = CartService.get_session_cart()
            product = Product.query.get(product_id)
            if not product:
                return False, "Product not found"
            if product.stock < quantity:
                return False, f"Insufficient stock. Only {product.stock} available."

            cart[str(product_id)] = quantity
            session['cart'] = cart
            session.modified = True
            return True, "Cart quantity updated."
        except Exception as e:
            return False, f"Error updating cart: {str(e)}"

    @staticmethod
    def clear_session_cart():
        """Clear the entire guest session cart."""
        try:
            session.pop('cart', None)
            session.modified = True
            return True, "Cart cleared successfully."
        except Exception as e:
            return False, f"Error clearing cart: {str(e)}"

    @staticmethod
    def get_session_cart_items():
        """Get all items from the guest session cart with details."""
        try:
            cart = CartService.get_session_cart()
            cart_items = []
            total = 0.0
            for product_id, quantity in cart.items():
                product = Product.query.get(int(product_id))
                if product:
                    item_total = product.price * quantity
                    cart_items.append({
                        'product_id': product.id,
                        'name': product.name,
                        'price': product.price,
                        'quantity': quantity,
                        'total': item_total,
                        'image': product.image,
                        'stock': product.stock,
                        'category': product.category
                    })
                    total += item_total
            return cart_items, total
        except Exception as e:
            print(f"Error getting session cart items: {e}")
            return [], 0.0

    @staticmethod
    def get_session_cart_count():
        """Get the total number of items in the guest session cart."""
        try:
            cart = CartService.get_session_cart()
            return sum(cart.values())
        except Exception as e:
            print(f"Error getting session cart count: {e}")
            return 0

    # Note: process_checkout and validate_cart methods would also need to be refactored
    # to work with the user_id and database cart if you implement checkout functionality. 