"""Shared utility helpers."""
from app import db
from app.models import Notification


def create_notification(user_id, title, message):
    """Create an in-app notification for a user."""
    notif = Notification(user_id=user_id, title=title, message=message)
    db.session.add(notif)
    # caller is responsible for db.session.commit()
