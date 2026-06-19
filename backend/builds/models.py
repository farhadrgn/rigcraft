from django.db import models
from django.contrib.auth.models import User
from components.models import GPU, CPU, Motherboard, CPUCooler, RAM, Storage, PSU, Case

# Create your models here.

class Build(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='builds')
    name = models.CharField(max_length=100)
    target_resolution = models.CharField(max_length=10, blank=True)
    gpu = models.ForeignKey(GPU, null=True, blank=True, on_delete=models.SET_NULL)
    cpu = models.ForeignKey(CPU, null=True, blank=True, on_delete=models.SET_NULL)
    motherboard = models.ForeignKey(Motherboard, null=True, blank=True, on_delete=models.SET_NULL)
    cooler = models.ForeignKey(CPUCooler, null=True, blank=True, on_delete=models.SET_NULL)
    ram = models.ForeignKey(RAM, null=True, blank=True, on_delete=models.SET_NULL)
    storage = models.ForeignKey(Storage, null=True, blank=True, on_delete=models.SET_NULL)
    psu = models.ForeignKey(PSU, null=True, blank=True, on_delete=models.SET_NULL)
    case = models.ForeignKey(Case, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} | {self.name}"