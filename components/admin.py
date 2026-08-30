from django.contrib import admin

from .models import GPU, CPU, Motherboard, CPUCooler, RAM, Storage, PSU, Case, GPUBenchmark

from compatibility.admin import BottleneckExceptionInline


class GPUAdmin(admin.ModelAdmin):
    inlines = [BottleneckExceptionInline]


admin.site.register(GPU, GPUAdmin)
admin.site.register(CPU)
admin.site.register(Motherboard)
admin.site.register(CPUCooler)
admin.site.register(RAM)
admin.site.register(Storage)
admin.site.register(PSU)
admin.site.register(Case)
admin.site.register(GPUBenchmark)