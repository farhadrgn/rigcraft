from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from components.models import GPU, CPU, Motherboard
from .models import Build

User = get_user_model()


class HomeViewTests(TestCase):
    def test_home_returns_200_and_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")


class BuilderViewTests(TestCase):
    fixtures = ["components_data.json"]

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.other_user = User.objects.create_user(username="other", password="testpass123")
        self.build = Build.objects.create(
            user=self.owner, name="My Rig", target_resolution="1440p"
        )

    def test_builder_get_returns_200_for_guest(self):
        response = self.client.get(reverse("builder"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "builds/builder.html")

    def test_builder_get_with_build_param_as_guest_does_not_crash(self):
        """Regression test for Bug 1: filtering by AnonymousUser must not raise."""
        response = self.client.get(reverse("builder"), {"build": self.build.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["initial_build"])

    def test_builder_get_with_own_build_param_prepopulates(self):
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("builder"), {"build": self.build.pk})
        self.assertEqual(response.context["initial_build"], self.build)

    def test_builder_get_with_other_users_build_param_does_not_leak(self):
        self.client.login(username="other", password="testpass123")
        response = self.client.get(reverse("builder"), {"build": self.build.pk})
        self.assertIsNone(response.context["initial_build"])


class BuilderSaveViewTests(TestCase):
    fixtures = ["components_data.json"]

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.other_user = User.objects.create_user(username="other", password="testpass123")
        self.cpu = CPU.objects.get(name="Intel Core i5-14600K")
        self.gpu = GPU.objects.get(name="NVIDIA GeForce RTX 5070")
        self.motherboard = Motherboard.objects.get(name="ROG STRIX Z790-A GAMING WIFI")

    def test_get_method_not_allowed(self):
        response = self.client.get(reverse("builder_save"))
        self.assertEqual(response.status_code, 405)

    def test_guest_redirected_to_login_with_message(self):
        response = self.client.post(reverse("builder_save"), {"name": "Test Build"}, follow=True)
        self.assertRedirects(response, reverse("login"))
        messages = list(response.context["messages"])
        self.assertTrue(any("log in" in str(m).lower() for m in messages))

    def test_creates_build_with_all_components_persisted(self):
        """Regression test for Bug 2: every selected component FK must
        actually be saved on creation, not just the base fields."""
        self.client.login(username="owner", password="testpass123")
        self.client.post(
            reverse("builder_save"),
            {
                "name": "New Rig",
                "target_resolution": "1440p",
                "cpu": self.cpu.pk,
                "gpu": self.gpu.pk,
                "motherboard": self.motherboard.pk,
            },
        )
        build = Build.objects.get(user=self.owner, name="New Rig")
        self.assertEqual(build.cpu, self.cpu)
        self.assertEqual(build.gpu, self.gpu)
        self.assertEqual(build.motherboard, self.motherboard)

    def test_updates_existing_build(self):
        self.client.login(username="owner", password="testpass123")
        build = Build.objects.create(user=self.owner, name="Old Name", target_resolution="1080p")
        self.client.post(
            reverse("builder_save"),
            {"build_id": build.pk, "name": "Updated Name", "target_resolution": "4K"},
        )
        build.refresh_from_db()
        self.assertEqual(build.name, "Updated Name")
        self.assertEqual(build.target_resolution, "4K")

    def test_cannot_update_other_users_build(self):
        self.client.login(username="other", password="testpass123")
        build = Build.objects.create(user=self.owner, name="Owner's Build", target_resolution="1080p")
        response = self.client.post(
            reverse("builder_save"),
            {"build_id": build.pk, "name": "Hijacked", "target_resolution": "4K"},
        )
        self.assertEqual(response.status_code, 404)


class BuildListViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.other_user = User.objects.create_user(username="other", password="testpass123")
        Build.objects.create(user=self.owner, name="Owner Build 1", target_resolution="1080p")
        Build.objects.create(user=self.owner, name="Owner Build 2", target_resolution="1440p")
        Build.objects.create(user=self.other_user, name="Other's Build", target_resolution="4K")

    def test_guest_redirected_to_login(self):
        response = self.client.get(reverse("build_list"))
        self.assertRedirects(response, reverse("login"))

    def test_only_shows_own_builds(self):
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("build_list"))
        names = {b.name for b in response.context["builds"]}
        self.assertEqual(names, {"Owner Build 1", "Owner Build 2"})


class BuildDetailViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.other_user = User.objects.create_user(username="other", password="testpass123")
        self.build = Build.objects.create(user=self.owner, name="My Rig", target_resolution="1440p")

    def test_guest_redirected_to_login(self):
        response = self.client.get(reverse("build_detail", args=[self.build.pk]))
        self.assertRedirects(response, reverse("login"))

    def test_owner_sees_200(self):
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("build_detail", args=[self.build.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "builds/detail.html")

    def test_non_owner_gets_404_not_403(self):
        self.client.login(username="other", password="testpass123")
        response = self.client.get(reverse("build_detail", args=[self.build.pk]))
        self.assertEqual(response.status_code, 404)


class BuildEditViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.other_user = User.objects.create_user(username="other", password="testpass123")
        self.build = Build.objects.create(user=self.owner, name="My Rig", target_resolution="1440p")

    def test_redirects_to_builder_with_build_param(self):
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("build_edit", args=[self.build.pk]))
        self.assertRedirects(response, f"/builder/?build={self.build.pk}")

    def test_non_owner_gets_404(self):
        self.client.login(username="other", password="testpass123")
        response = self.client.get(reverse("build_edit", args=[self.build.pk]))
        self.assertEqual(response.status_code, 404)


class BuildDeleteViewTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.other_user = User.objects.create_user(username="other", password="testpass123")
        self.build = Build.objects.create(user=self.owner, name="My Rig", target_resolution="1440p")

    def test_get_method_not_allowed(self):
        self.client.login(username="owner", password="testpass123")
        response = self.client.get(reverse("build_delete", args=[self.build.pk]))
        self.assertEqual(response.status_code, 405)

    def test_owner_can_delete_via_post(self):
        self.client.login(username="owner", password="testpass123")
        response = self.client.post(reverse("build_delete", args=[self.build.pk]))
        self.assertRedirects(response, reverse("build_list"))
        self.assertFalse(Build.objects.filter(pk=self.build.pk).exists())

    def test_non_owner_gets_404(self):
        self.client.login(username="other", password="testpass123")
        response = self.client.post(reverse("build_delete", args=[self.build.pk]))
        self.assertEqual(response.status_code, 404)