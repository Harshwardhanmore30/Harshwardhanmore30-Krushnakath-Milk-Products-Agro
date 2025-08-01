from models.database import db, Order, OrderItem, Product, Cart, CartItem
from services.cart_service import CartService

class OrderService:
    @staticmethod
    def create_order(user_id, shipping_address, transaction_id, payment_screenshot_filename):
        """
        Create an order from the user's cart, save it to the database,
        and clear the cart.
        """
        try:
            # Get all items from the user's database cart
            cart_items, total_amount = CartService.get_cart_items(user_id)

            if not cart_items:
                return False, "Cannot create order from an empty cart."

            # Create the main order record
            new_order = Order(
                user_id=user_id,
                total_amount=total_amount,
                shipping_address=shipping_address,
                transaction_id=transaction_id,
                payment_screenshot=payment_screenshot_filename,
                status='Pending Verification' # Initial status
            )
            db.session.add(new_order)
            
            # Transfer items from cart to order items and update stock
            for item in cart_items:
                product = Product.query.get(item['product_id'])
                if not product or product.stock < item['quantity']:
                    db.session.rollback()
                    return False, f"Not enough stock for {item['name']}."
                
                # Create a new OrderItem
                order_item = OrderItem(
                    order=new_order,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    price=item['price'] # Price at the time of purchase
                )
                db.session.add(order_item)
                
                # Decrement stock
                product.stock -= item['quantity']
            
            # Clear the user's cart
            cart = Cart.query.filter_by(user_id=user_id).first()
            if cart:
                CartItem.query.filter_by(cart_id=cart.id).delete()

            db.session.commit()
            return True, "Order created successfully."

        except Exception as e:
            db.session.rollback()
            return False, f"An error occurred while creating the order: {str(e)}"

    @staticmethod
    def get_orders_by_user(user_id):
        """Fetch all orders for a specific user."""
        return Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_all_orders():
        """Fetch all orders for the admin panel."""
        return Order.query.order_by(Order.created_at.desc()).all()
        
    @staticmethod
    def update_order_status(order_id, new_status):
        """Update the status of an order."""
        try:
            order = Order.query.get(order_id)
            if not order:
                return False, "Order not found."
            
            order.status = new_status
            db.session.commit()
            return True, f"Order {order_id} status updated to {new_status}."
        except Exception as e:
            db.session.rollback()
            return False, f"Error updating order status: {str(e)}" 