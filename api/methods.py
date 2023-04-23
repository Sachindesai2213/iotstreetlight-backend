from .models import ActivityLog


def log_activity(user_id, type):
    activity = ActivityLog(
        user_id=user_id,
        type=type
    )
    activity.save()
