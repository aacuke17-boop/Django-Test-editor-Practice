from accounts.models import ANONYMOUS_EMAIL


def format_duration(delta):
    if delta is None:
        return "-"
    total = max(0, int(delta.total_seconds()))
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def participant_label(user):
    if user is None:
        return "Deleted user"
    if user.email == ANONYMOUS_EMAIL:
        return "Anonymous"
    return user.username
