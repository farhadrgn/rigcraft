from django.contrib import admin
from .models import GPU, CPU, Motherboard, CPUCooler, RAM, Storage, PSU, Case

# Register your models here.
admin.site.register(GPU)
admin.site.register(CPU)
admin.site.register(Motherboard)
admin.site.register(CPUCooler)
admin.site.register(RAM)
admin.site.register(Storage)
admin.site.register(PSU)
admin.site.register(Case)