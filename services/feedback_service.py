from models.database import db, Feedback
from datetime import datetime

class FeedbackService:
    """Service class for feedback operations"""
    
    @staticmethod
    def create_feedback(name, email, message):
        """Create a new feedback entry"""
        try:
            feedback = Feedback(
                name=name,
                email=email,
                message=message
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            return True, "Feedback submitted successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error submitting feedback: {str(e)}"
    
    @staticmethod
    def get_all_feedback():
        """Get all feedback entries"""
        try:
            feedback_list = Feedback.query.order_by(Feedback.created_at.desc()).all()
            return feedback_list
        except Exception as e:
            print(f"Error fetching feedback: {e}")
            return []
    
    @staticmethod
    def get_feedback_by_id(feedback_id):
        """Get feedback by ID"""
        try:
            feedback = Feedback.query.get(feedback_id)
            return feedback
        except Exception as e:
            print(f"Error fetching feedback {feedback_id}: {e}")
            return None
    
    @staticmethod
    def delete_feedback(feedback_id):
        """Delete a feedback entry"""
        try:
            feedback = Feedback.query.get(feedback_id)
            if not feedback:
                return False, "Feedback not found"
            
            db.session.delete(feedback)
            db.session.commit()
            
            return True, "Feedback deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting feedback: {str(e)}"
    
    @staticmethod
    def get_feedback_count():
        """Get total number of feedback entries"""
        try:
            count = Feedback.query.count()
            return count
        except Exception as e:
            print(f"Error getting feedback count: {e}")
            return 0
    
    @staticmethod
    def get_recent_feedback(limit=5):
        """Get recent feedback entries"""
        try:
            recent_feedback = Feedback.query.order_by(
                Feedback.created_at.desc()
            ).limit(limit).all()
            return recent_feedback
        except Exception as e:
            print(f"Error fetching recent feedback: {e}")
            return [] 