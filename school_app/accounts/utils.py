from accounts.models import UserProfile
from groups.models import GroupProfile



def get_affiliated_users(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.affiliated_users.all()
    except UserProfile.DoesNotExist:
        return []
