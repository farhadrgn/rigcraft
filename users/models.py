from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model with no additional fields.

    Defined explicitly (instead of using Django's default User) so the
    project can add fields later without a disruptive database reset.
    """
    pass