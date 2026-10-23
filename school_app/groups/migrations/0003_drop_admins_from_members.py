from django.db import migrations


def drop_admins_from_members(apps, schema_editor):
    # Admins take precedence: remove plain memberships of people who are
    # already admins of the same group.
    GroupProfile = apps.get_model("groups", "GroupProfile")
    for profile in GroupProfile.objects.all():
        profile.members.remove(*profile.admins.all())


class Migration(migrations.Migration):
    dependencies = [("groups", "0002_groupprofile_description")]

    operations = [migrations.RunPython(drop_admins_from_members, migrations.RunPython.noop)]
