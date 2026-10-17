import tempfile
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from groups.models import GroupProfile

CSV_HEADER = "name,description,admins,members\n"


class ImportGroupsTests(TestCase):
    def setUp(self):
        for username in ["teacher", "lucy", "max", "tom"]:
            User.objects.create_user(username=username)
        self.tmp = Path(tempfile.mkdtemp())

    def run_import(self, rows):
        csv_file = self.tmp / "groups.csv"
        csv_file.write_text(CSV_HEADER + rows)
        call_command("import_groups", str(csv_file), stdout=open("/dev/null", "w"))

    def usernames(self, users):
        return sorted(users.values_list("username", flat=True))

    def test_creates_groups_with_admins_and_members(self):
        self.run_import(
            "Class 1A,First grade,teacher,lucy;tom\n"
            "Class 2B,Second grade,teacher,max;tom\n"
        )
        first = GroupProfile.objects.get(group__name="Class 1A")
        second = GroupProfile.objects.get(group__name="Class 2B")

        self.assertEqual(first.description, "First grade")
        self.assertEqual(self.usernames(first.admins), ["teacher"])
        self.assertEqual(self.usernames(first.members), ["lucy", "tom"])
        self.assertEqual(self.usernames(second.members), ["max", "tom"])

    def test_skips_existing_groups(self):
        Group.objects.create(name="Class 1A")
        self.run_import("Class 1A,First grade,teacher,lucy\n")
        self.assertFalse(GroupProfile.objects.exists())

    def test_unknown_user_rolls_back_whole_import(self):
        with self.assertRaises(CommandError):
            self.run_import(
                "Class 1A,First grade,teacher,lucy\n"
                "Class 2B,Second grade,teacher,nobody\n"
            )
        self.assertFalse(Group.objects.exists())


class GroupListFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="lucy", password="pw")
        teacher = User.objects.create_user(username="teacher")
        self.member_of = self.make_group("Class 1A", members=[self.user])
        self.admin_of = self.make_group("Class 1A Parents", admins=[self.user])
        self.other = self.make_group("Class 2B", admins=[teacher])
        self.client.force_login(self.user)

    def make_group(self, name, admins=(), members=()):
        profile = GroupProfile.objects.create(group=Group.objects.create(name=name))
        profile.admins.add(*admins)
        profile.members.add(*members)
        return profile

    def listed(self, url):
        return list(self.client.get(url).context["groups"])

    def test_shows_only_own_groups_by_default(self):
        self.assertEqual(
            self.listed(reverse("groups")), [self.member_of, self.admin_of]
        )

    def test_show_all_lists_every_group(self):
        self.assertEqual(
            self.listed(reverse("groups") + "?show=all"),
            [self.member_of, self.admin_of, self.other],
        )

    def test_detail_page_uses_the_same_filter(self):
        url = reverse("group_detail", args=[self.other.pk])
        self.assertEqual(self.listed(url), [self.member_of, self.admin_of])
        self.assertEqual(len(self.listed(url + "?show=all")), 3)


class GroupListAffiliateTests(TestCase):
    def setUp(self):
        self.guardian = User.objects.create_user(username="tom", password="pw")
        self.child = User.objects.create_user(username="lucy", first_name="Lucy")
        self.guardian.profile.affiliated_users.add(self.child)
        self.child_class = GroupProfile.objects.create(
            group=Group.objects.create(name="Class 1A")
        )
        self.child_class.members.add(self.child)
        self.client.force_login(self.guardian)

    def listed(self):
        return list(self.client.get(reverse("groups")).context["groups"])

    def test_shows_groups_of_affiliated_users(self):
        groups = self.listed()
        self.assertEqual(groups, [self.child_class])
        self.assertEqual(groups[0].connected_users, [self.child])

    def test_lists_every_connected_person_on_a_shared_group(self):
        self.child_class.admins.add(self.guardian)
        response = self.client.get(reverse("groups"))
        self.assertEqual(
            response.context["groups"][0].connected_users, [self.guardian, self.child]
        )
        self.assertContains(response, "You")
        self.assertContains(response, "Lucy")


class GroupEditPermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin_t", password="pw")
        self.member = User.objects.create_user(username="member", password="pw")
        self.outsider = User.objects.create_user(username="outsider", password="pw")
        self.group = GroupProfile.objects.create(group=Group.objects.create(name="Class 1A"))
        self.group.admins.add(self.admin)
        self.group.members.add(self.member)
        self.url = reverse("group_edit", args=[self.group.pk])

    def post(self, user, admins, members):
        self.client.force_login(user)
        return self.client.post(self.url, {"description": "New", "admins": [u.pk for u in admins], "members": [u.pk for u in members]})

    def test_admin_can_change_admins_and_members(self):
        response = self.post(self.admin, admins=[self.admin, self.member], members=[self.outsider])
        self.assertRedirects(response, reverse("group_detail", args=[self.group.pk]), fetch_redirect_response=False)
        self.assertEqual(set(self.group.admins.all()), {self.admin, self.member})
        self.assertEqual(list(self.group.members.all()), [self.outsider])

    def test_members_and_outsiders_cannot_edit(self):
        for user in (self.member, self.outsider):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.post(user, admins=[user], members=[user]).status_code, 403)
        self.assertEqual(list(self.group.admins.all()), [self.admin])
        self.assertEqual(list(self.group.members.all()), [self.member])

    def test_anonymous_is_sent_to_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.get(reverse("group_create")).status_code, 302)

    def test_group_keeps_at_least_one_admin(self):
        response = self.post(self.admin, admins=[], members=[self.member])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A group needs at least one admin.")
        self.assertEqual(list(self.group.admins.all()), [self.admin])

    def test_edit_buttons_only_for_admins(self):
        self.client.force_login(self.member)
        self.assertNotContains(self.client.get(reverse("groups")), self.url)
        self.assertNotContains(self.client.get(reverse("group_detail", args=[self.group.pk])), self.url)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("groups")), self.url)
        self.assertContains(self.client.get(reverse("group_detail", args=[self.group.pk])), self.url)
