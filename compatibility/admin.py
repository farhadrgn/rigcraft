# compatibility/admin.py
from django.contrib import admin
from .models import BottleneckException


class BottleneckExceptionInline(admin.TabularInline):
    model = BottleneckException
    extra = 1
    fields = ["cpu", "resolution", "gpu_utilization_percent"]