from django.contrib.auth.forms import UserCreationForm

from .models import User


class RigCraftUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User