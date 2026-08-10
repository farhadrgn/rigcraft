from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class RegisterViewTests(TestCase):
    def test_get_returns_form(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/register.html")

    def test_valid_submission_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "password1": "a-strong-password-123",
                "password2": "a-strong-password-123",
            },
        )
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_is_redirected_away_from_register(self):
        User.objects.create_user(username="existing", password="testpass123")
        self.client.login(username="existing", password="testpass123")
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("home"))


class LoginLogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="someone", password="testpass123")

    def test_correct_credentials_redirect_to_home(self):
        response = self.client.post(
            reverse("login"), {"username": "someone", "password": "testpass123"}
        )
        self.assertRedirects(response, reverse("home"))

    def test_incorrect_credentials_rerender_form_with_error(self):
        response = self.client.post(
            reverse("login"), {"username": "someone", "password": "wrong-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")
        self.assertFalse(response.context["user"].is_authenticated)

    def test_logout_redirects_to_home(self):
        self.client.login(username="someone", password="testpass123")
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))