from flask import Blueprint, render_template, redirect, url_for, flash, session, make_response
from services.order_service import OrderService
from services.auth_service import AuthService
from services.invoice_service import InvoiceService
from models.database import Order
from functools import wraps

order_bp = Blueprint('order', __name__)

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not AuthService.is_authenticated():
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@order_bp.route('/my-orders')
@login_required
def my_orders():
    """Display the current user's order history."""
    user_id = session.get('user_id')
    orders = OrderService.get_orders_by_user(user_id)
    return render_template('my_orders.html', orders=orders)

@order_bp.route('/download-invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    """Download PDF invoice for an order."""
    try:
        # Get the order and verify it belongs to the current user
        order = Order.query.get_or_404(order_id)
        user_id = session.get('user_id')

        if order.user_id != user_id:
            flash('You can only download invoices for your own orders.', 'error')
            return redirect(url_for('order.my_orders'))

        # Generate PDF invoice
        pdf_data, error = InvoiceService.generate_invoice_pdf(order_id)

        if error:
            flash(f'Error generating invoice: {error}', 'error')
            return redirect(url_for('order.my_orders'))

        # Create response with PDF
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{InvoiceService.get_invoice_filename(order_id)}"'

        return response

    except Exception as e:
        flash(f'Error downloading invoice: {str(e)}', 'error')
        return redirect(url_for('order.my_orders'))