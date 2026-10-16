from accounts.models import UserProfile
from groups.models import GroupProfile


def get_affiliated_users(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.affiliated_users.all()
    except UserProfile.DoesNotExist:
        return []


def get_group_profiles_for_users_list(user_list):
    group_profiles = set()
    for user in user_list:
        try:
            profile = UserProfile.objects.get(user=user)
            user_groups = profile.group_profiles
            group_profiles.update(user_groups)
        except UserProfile.DoesNotExist:
            continue
    return list(group_profiles)
