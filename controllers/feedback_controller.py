from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.feedback_service import FeedbackService
from functools import wraps

feedback_bp = Blueprint('feedback', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session
        if not session.get('username') or session.get('user_type') != 'admin':
            flash('Admin access required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@feedback_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        success, msg = FeedbackService.create_feedback(name, email, message)
        if success:
            flash(msg, 'success')
            return redirect(url_for('product.index'))
        else:
            flash(msg, 'error')
    return render_template('feedback.html')

@feedback_bp.route('/admin/feedback')
@admin_required
def admin_feedback():
    feedbacks = FeedbackService.get_all_feedback()
    return render_template('admin_feedback.html', feedbacks=feedbacks)

@feedback_bp.route('/admin/feedback/delete/<int:feedback_id>', methods=['POST'])
@admin_required
def delete_feedback(feedback_id):
    success, msg = FeedbackService.delete_feedback(feedback_id)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'error')
    return redirect(url_for('feedback.admin_feedback')) 