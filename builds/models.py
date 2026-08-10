from django.conf import settings
from django.db import models

from components.models import (
    GPU,
    CPU,
    Motherboard,
    CPUCooler,
    RAM,
    Storage,
    PSU,
    Case,
    GPUBenchmark,
)


class Build(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="builds"
    )
    name = models.CharField(max_length=100)
    target_resolution = models.CharField(
        max_length=10, choices=GPUBenchmark.Resolution.choices
    )

    gpu = models.ForeignKey(GPU, on_delete=models.SET_NULL, null=True, blank=True)
    cpu = models.ForeignKey(CPU, on_delete=models.SET_NULL, null=True, blank=True)
    motherboard = models.ForeignKey(
        Motherboard, on_delete=models.SET_NULL, null=True, blank=True
    )
    cooler = models.ForeignKey(CPUCooler, on_delete=models.SET_NULL, null=True, blank=True)
    ram = models.ForeignKey(RAM, on_delete=models.SET_NULL, null=True, blank=True)
    storage = models.ForeignKey(Storage, on_delete=models.SET_NULL, null=True, blank=True)
    psu = models.ForeignKey(PSU, on_delete=models.SET_NULL, null=True, blank=True)
    case = models.ForeignKey(Case, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} ({self.user})"