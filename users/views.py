from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RigCraftUserCreationForm


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RigCraftUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RigCraftUserCreationForm()

    return render(request, "registration/register.html", {"form": form})