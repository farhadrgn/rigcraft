from django.urls import path
from .views import CompatibilityCheckView

urlpatterns = [
    path('compatibility/check/', CompatibilityCheckView.as_view(), name='compatibility-check'),
]